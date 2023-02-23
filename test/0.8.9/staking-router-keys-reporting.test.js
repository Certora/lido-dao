const { artifacts, contract, ethers } = require('hardhat')
const { EvmSnapshot } = require('../helpers/blockchain')
const { assert } = require('../helpers/assert')
const { hex, hexConcat, toNum } = require('../helpers/utils')

const StakingRouter = artifacts.require('StakingRouterMock.sol')
const StakingModuleMock = artifacts.require('StakingModuleMock.sol')
const DepositContractMock = artifacts.require('DepositContractMock.sol')

contract('StakingRouter', ([deployer, lido, admin]) => {
  const evmSnapshot = new EvmSnapshot(ethers.provider)

  let depositContract, router
  let module1, module2

  before(async () => {
    depositContract = await DepositContractMock.new({ from: deployer })
    router = await StakingRouter.new(depositContract.address, { from: deployer })
    ;[module1, module2] = await Promise.all([
      StakingModuleMock.new({ from: deployer }),
      StakingModuleMock.new({ from: deployer }),
    ])

    const wc = '0x'.padEnd(66, '1234')
    await router.initialize(admin, lido, wc, { from: deployer })

    await router.grantRole(await router.MANAGE_WITHDRAWAL_CREDENTIALS_ROLE(), admin, { from: admin })
    await router.grantRole(await router.STAKING_MODULE_PAUSE_ROLE(), admin, { from: admin })
    await router.grantRole(await router.STAKING_MODULE_MANAGE_ROLE(), admin, { from: admin })
    await router.grantRole(await router.REPORT_EXITED_VALIDATORS_ROLE(), admin, { from: admin })
  })

  const getCallInfo = async (sModule) => {
    const callCountToNum = (callInfo) => {
      return { ...callInfo, callCount: +callInfo.callCount }
    }
    return {
      updateStuckValidatorsCount: callCountToNum(await sModule.lastCall_updateStuckValidatorsCount()),
      updateExitedValidatorsCount: callCountToNum(await sModule.lastCall_updateExitedValidatorsCount()),
      onExitedAndStuckValidatorsCountsUpdated: {
        callCount: +(await sModule.callCount_onExitedAndStuckValidatorsCountsUpdated()),
      },
    }
  }

  before(async () => {
    for (const moduleI of [module1, module2]) {
      const callInfo = await getCallInfo(moduleI)
      assert.equal(callInfo.updateStuckValidatorsCount.callCount, 0)
      assert.equal(callInfo.updateExitedValidatorsCount.callCount, 0)
      assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
    }
  })

  const snapshot = () => evmSnapshot.make()
  const revert = () => evmSnapshot.revert()

  describe('exited/stuck keys reporting', () => {
    describe('one staking module', async () => {
      before(snapshot)
      after(revert)

      let module1Id

      it('adding the only module', async () => {
        await router.addStakingModule(
          'module 1',
          module1.address,
          10_000, // target share 100 %
          1_000, // module fee 10 %
          5_000, // treasury fee 5 %
          { from: admin }
        )
        module1Id = +(await router.getStakingModuleIds())[0]
      })

      it('initially, router assumes no staking modules have exited validators', async () => {
        const info = await router.getStakingModule(module1Id)
        assert.equals(info.exitedValidatorsCount, 0)

        const totalExited = await router.getExitedValidatorsCountAcrossAllModules()
        assert.equals(totalExited, 0)
      })

      it('reporting total exited validators of a non-existent module reverts', async () => {
        await assert.reverts(
          router.updateExitedValidatorsCountByStakingModule([module1Id + 1], [1], { from: admin }),
          'StakingModuleUnregistered()'
        )
        await assert.reverts(
          router.updateExitedValidatorsCountByStakingModule([module1Id, module1Id + 1], [1, 1], { from: admin }),
          'StakingModuleUnregistered()'
        )
      })

      it('reporting module 1 to have total 3 exited validators', async () => {
        await router.updateExitedValidatorsCountByStakingModule([module1Id], [3], { from: admin })
      })

      it('staking module info gets updated', async () => {
        const info = await router.getStakingModule(module1Id)
        assert.equals(info.exitedValidatorsCount, 3)
      })

      it('exited validators count accross all modules gets updated', async () => {
        const totalExited = await router.getExitedValidatorsCountAcrossAllModules()
        assert.equals(totalExited, 3)
      })

      it('no functions were called on the module', async () => {
        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it(`calling onValidatorsCountsByNodeOperatorReportingFinished doesn't call anything on the module`, async () => {
        await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('reporting stuck validators by node op of a non-existent module reverts', async () => {
        const nonExistentModuleId = module1Id + 1
        const nodeOpIdsData = hexConcat(hex(1, 8))
        const validatorsCountsData = hexConcat(hex(1, 16))
        await assert.reverts(
          router.reportStakingModuleStuckValidatorsCountByNodeOperator(
            nonExistentModuleId,
            nodeOpIdsData,
            validatorsCountsData,
            { from: admin }
          ),
          'StakingModuleUnregistered()'
        )
      })

      it('passing empty data while reporting stuck validators by node operator reverts', async () => {
        await assert.reverts(
          router.reportStakingModuleStuckValidatorsCountByNodeOperator(module1Id, '0x', '0x', { from: admin }),
          'InvalidReportData(1)'
        )
      })

      const mismatchedLengthData = [
        {
          nodeOpIds: '0x',
          validatorsCounts: hexConcat(hex(1, 16)),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8)),
          validatorsCounts: '0x',
        },
        {
          nodeOpIds: hexConcat(hex(1, 8), hex(2, 8)),
          validatorsCounts: hexConcat(hex(1, 16)),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8)),
          validatorsCounts: hexConcat(hex(1, 16), hex(1, 16)),
        },
      ]

      it('passing data with mismatched length while reporting stuck validators by node operator reverts', async () => {
        await Promise.all(
          mismatchedLengthData.map((data) =>
            assert.reverts(
              router.reportStakingModuleStuckValidatorsCountByNodeOperator(
                module1Id,
                data.nodeOpIds,
                data.validatorsCounts,
                { from: admin }
              ),
              'InvalidReportData(2)'
            )
          )
        )
      })

      const invalidLengthData = [
        {
          nodeOpIds: '0x00',
          validatorsCounts: '0x',
        },
        {
          nodeOpIds: '0x',
          validatorsCounts: '0x00',
        },
        {
          nodeOpIds: '0x00',
          validatorsCounts: '0x00',
        },
        {
          nodeOpIds: hexConcat(hex(1, 8), '0x00'),
          validatorsCounts: hexConcat(hex(1, 16)),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8), '0x00'),
          validatorsCounts: hexConcat(hex(1, 16), '0x00'),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8)),
          validatorsCounts: hexConcat(hex(1, 16), '0x00'),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8), hex(2, 8), '0x00'),
          validatorsCounts: hexConcat(hex(1, 16)),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8), hex(2, 8)),
          validatorsCounts: hexConcat(hex(1, 16), '0x00'),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8), '0x00'),
          validatorsCounts: hexConcat(hex(1, 16), hex(1, 16)),
        },
        {
          nodeOpIds: hexConcat(hex(1, 8)),
          validatorsCounts: hexConcat(hex(1, 16), hex(1, 16), '0x00'),
        },
      ]

      it('passing data with invalid length while reporting stuck validators by node operator reverts', async () => {
        await Promise.all(
          invalidLengthData.map((data) =>
            assert.reverts(
              router.reportStakingModuleStuckValidatorsCountByNodeOperator(
                module1Id,
                data.nodeOpIds,
                data.validatorsCounts,
                { from: admin }
              ),
              'InvalidReportData(3)'
            )
          )
        )
      })

      it('reporting stuck validators by node operator passes the info to the module', async () => {
        const nodeOpIds = [3, 5]
        const validatorsCounts = [1, 1]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleStuckValidatorsCountByNodeOperator(
          module1Id,
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo.updateStuckValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo.updateStuckValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it(`calling onValidatorsCountsByNodeOperatorReportingFinished still doesn't call anything on the module`, async () => {
        await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 0)
      })

      it('reporting exited validators by node op of a non-existent module reverts', async () => {
        const nonExistentModuleId = module1Id + 1
        const nodeOpIdsData = hexConcat(hex(1, 8))
        const validatorsCountsData = hexConcat(hex(1, 16))
        await assert.reverts(
          router.reportStakingModuleExitedValidatorsCountByNodeOperator(
            nonExistentModuleId,
            nodeOpIdsData,
            validatorsCountsData,
            { from: admin }
          ),
          'StakingModuleUnregistered()'
        )
      })

      it('passing empty data while reporting exited validators by node operator reverts', async () => {
        await assert.reverts(
          router.reportStakingModuleExitedValidatorsCountByNodeOperator(module1Id, '0x', '0x', { from: admin }),
          'InvalidReportData(1)'
        )
      })

      it('passing data with mismatched length while reporting exited validators by node operator reverts', async () => {
        await Promise.all(
          mismatchedLengthData.map((data) =>
            assert.reverts(
              router.reportStakingModuleExitedValidatorsCountByNodeOperator(
                module1Id,
                data.nodeOpIds,
                data.validatorsCounts,
                { from: admin }
              ),
              'InvalidReportData(2)'
            )
          )
        )
      })

      it('passing data with invalid length while reporting exited validators by node operator reverts', async () => {
        await Promise.all(
          invalidLengthData.map((data) =>
            assert.reverts(
              router.reportStakingModuleExitedValidatorsCountByNodeOperator(
                module1Id,
                data.nodeOpIds,
                data.validatorsCounts,
                { from: admin }
              ),
              'InvalidReportData(3)'
            )
          )
        )
      })

      it('reporting exited validators by node operator (total 2) passes the info to the module', async () => {
        const nodeOpIds = [1, 2]
        const validatorsCounts = [1, 1]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleExitedValidatorsCountByNodeOperator(
          module1Id,
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)

        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 1)
        assert.equal(callInfo.updateExitedValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo.updateExitedValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('the staking module updates its internal total exited counter to 2', async () => {
        await module1.setTotalExitedValidatorsCount(2)
      })

      it(`router's view on exited validators count accross all modules stays the same`, async () => {
        const totalExited = await router.getExitedValidatorsCountAcrossAllModules()
        assert.equals(totalExited, 3)
      })

      it(`calling onValidatorsCountsByNodeOperatorReportingFinished still doesn't call anything on the module`, async () => {
        await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 1)
      })

      it('reporting one more exited validator by node operator passes the info to the module', async () => {
        const nodeOpIds = [3]
        const validatorsCounts = [1]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleExitedValidatorsCountByNodeOperator(
          module1Id,
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo = await getCallInfo(module1)
        assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)

        assert.equal(callInfo.updateExitedValidatorsCount.callCount, 2)
        assert.equal(callInfo.updateExitedValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo.updateExitedValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('the staking module updates its internal total exited counter to 3', async () => {
        await module1.setTotalExitedValidatorsCount(3)
      })

      // eslint-disable-next-line prettier/prettier
      it(`now that exited validators totals in the router and in the module match, calling` +
          `onValidatorsCountsByNodeOperatorReportingFinished calls ` +
          `onExitedAndStuckValidatorsCountsUpdated on the module`,
        async () => {
          await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

          const callInfo = await getCallInfo(module1)
          assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 1)

          assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)
          assert.equal(callInfo.updateExitedValidatorsCount.callCount, 2)
        }
      )

      // eslint-disable-next-line prettier/prettier
      it(`calling onValidatorsCountsByNodeOperatorReportingFinished one more time calls ` +
          `onExitedAndStuckValidatorsCountsUpdated on the module again`,
        async () => {
          await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

          const callInfo = await getCallInfo(module1)
          assert.equal(callInfo.onExitedAndStuckValidatorsCountsUpdated.callCount, 2)

          assert.equal(callInfo.updateStuckValidatorsCount.callCount, 1)
          assert.equal(callInfo.updateExitedValidatorsCount.callCount, 2)
        }
      )
    })

    describe('two staking modules', async () => {
      before(snapshot)
      after(revert)

      let moduleIds

      it('adding the two modules', async () => {
        await router.addStakingModule(
          'module 1',
          module1.address,
          10_000, // 100 % _targetShare
          1_000, // 10 % _moduleFee
          5_000, // 50 % _treasuryFee
          { from: admin }
        )
        await router.addStakingModule(
          'module 2',
          module2.address,
          200, // 2 % _targetShare
          5_000, // 50 % _moduleFee
          0, // 0 % _treasuryFee
          { from: admin }
        )
        moduleIds = toNum(await router.getStakingModuleIds())
      })

      it('initially, router assumes no staking modules have exited validators', async () => {
        const info1 = await router.getStakingModule(moduleIds[0])
        assert.equals(info1.exitedValidatorsCount, 0)

        const info2 = await router.getStakingModule(moduleIds[1])
        assert.equals(info2.exitedValidatorsCount, 0)

        const totalExited = await router.getExitedValidatorsCountAcrossAllModules()
        assert.equals(totalExited, 0)
      })

      it('reporting 3 exited keys total for module 1 and 2 exited keys total for module 2', async () => {
        await router.updateExitedValidatorsCountByStakingModule(moduleIds, [3, 2], { from: admin })
      })

      it('staking modules info gets updated', async () => {
        const info1 = await router.getStakingModule(moduleIds[0])
        assert.equals(info1.exitedValidatorsCount, 3)

        const info2 = await router.getStakingModule(moduleIds[1])
        assert.equals(info2.exitedValidatorsCount, 2)
      })

      it('exited validators count accross all modules gets updated', async () => {
        const totalExited = await router.getExitedValidatorsCountAcrossAllModules()
        assert.equals(totalExited, 5)
      })

      it('no functions were called on any module', async () => {
        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it(`calling onValidatorsCountsByNodeOperatorReportingFinished doesn't call anything on any module`, async () => {
        await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('reporting stuck validators by node operator passes the info to the module 1', async () => {
        const nodeOpIds = [1]
        const validatorsCounts = [3]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleStuckValidatorsCountByNodeOperator(
          moduleIds[0],
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.updateStuckValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo1.updateStuckValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 0)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('reporting stuck validators by node operator passes the info to the module 2', async () => {
        const nodeOpIds = [33]
        const validatorsCounts = [7]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleStuckValidatorsCountByNodeOperator(
          moduleIds[1],
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo2.updateStuckValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo2.updateStuckValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it(`calling onValidatorsCountsByNodeOperatorReportingFinished still doesn't call anything on any module`, async () => {
        await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('reporting exited validators by node operator passes the info to the module 1', async () => {
        const nodeOpIds = [3, 4]
        const validatorsCounts = [1, 1]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleExitedValidatorsCountByNodeOperator(
          moduleIds[0],
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 1)
        assert.equal(callInfo1.updateExitedValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo1.updateExitedValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('the staking module 1 updates its internal total exited counter to 2', async () => {
        await module1.setTotalExitedValidatorsCount(2)
      })

      it(`calling onValidatorsCountsByNodeOperatorReportingFinished still doesn't call anything on any module`, async () => {
        await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 1)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 0)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('reporting exited validators by node operator passes the info to the module 2', async () => {
        const nodeOpIds = [20]
        const validatorsCounts = [1]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleExitedValidatorsCountByNodeOperator(
          moduleIds[1],
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 1)
        assert.equal(callInfo2.updateExitedValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo2.updateExitedValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 1)
        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
      })

      it('the staking module 2 updates its internal total exited counter to 2', async () => {
        await module2.setTotalExitedValidatorsCount(2)
      })

      // eslint-disable-next-line prettier/prettier
      it(`now that router's view on exited validators total match the module 2's view,` +
          `calling onValidatorsCountsByNodeOperatorReportingFinished calls ` +
          `onExitedAndStuckValidatorsCountsUpdated on the module 2`,
        async () => {
          await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

          const callInfo1 = await getCallInfo(module1)
          const callInfo2 = await getCallInfo(module2)

          assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)
          assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 1)

          assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 1)
          assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)

          assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 1)
          assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        }
      )

      it('reporting exited validators by node operator passes the info to the module 1', async () => {
        const nodeOpIds = [55]
        const validatorsCounts = [1]

        const nodeOpIdsData = hexConcat(...nodeOpIds.map((i) => hex(i, 8)))
        const validatorsCountsData = hexConcat(...validatorsCounts.map((c) => hex(c, 16)))

        await router.reportStakingModuleExitedValidatorsCountByNodeOperator(
          moduleIds[0],
          nodeOpIdsData,
          validatorsCountsData,
          { from: admin }
        )

        const callInfo1 = await getCallInfo(module1)
        assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 2)
        assert.equal(callInfo1.updateExitedValidatorsCount.nodeOperatorIds, nodeOpIdsData)
        assert.equal(callInfo1.updateExitedValidatorsCount.validatorsCounts, validatorsCountsData)

        assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 0)

        const callInfo2 = await getCallInfo(module2)
        assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 1)
        assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 1)
      })

      it('the staking module 1 updates its internal total exited counter to 3', async () => {
        await module1.setTotalExitedValidatorsCount(3)
      })

      // eslint-disable-next-line prettier/prettier
      it(`now that router's view on exited validators total match the both modules' view,` +
          `calling onValidatorsCountsByNodeOperatorReportingFinished calls ` +
          `onExitedAndStuckValidatorsCountsUpdated on both modules`,
        async () => {
          await router.onValidatorsCountsByNodeOperatorReportingFinished({ from: admin })

          const callInfo1 = await getCallInfo(module1)
          const callInfo2 = await getCallInfo(module2)

          assert.equal(callInfo1.onExitedAndStuckValidatorsCountsUpdated.callCount, 1)
          assert.equal(callInfo2.onExitedAndStuckValidatorsCountsUpdated.callCount, 2)

          assert.equal(callInfo1.updateExitedValidatorsCount.callCount, 2)
          assert.equal(callInfo1.updateStuckValidatorsCount.callCount, 1)

          assert.equal(callInfo2.updateExitedValidatorsCount.callCount, 1)
          assert.equal(callInfo2.updateStuckValidatorsCount.callCount, 1)
        }
      )
    })
  })
})
