const { contract, ethers, artifacts, web3 } = require('hardhat')
const { assert } = require('../helpers/assert')
const { impersonate } = require('../helpers/blockchain')
const { e9, e18, e27, toBN } = require('../helpers/utils')
const { legacyOracleFactory } = require('../helpers/factories')

const OssifiableProxy = artifacts.require('OssifiableProxy')
const LegacyOracle = artifacts.require('LegacyOracle')
const MockLegacyOracle = artifacts.require('MockLegacyOracle')

const LegacyOracleAbi = require('../../lib/abi/LegacyOracle.json')

const {
  deployAccountingOracleSetup,
  initAccountingOracle,
  EPOCHS_PER_FRAME,
  SLOTS_PER_EPOCH,
  SECONDS_PER_SLOT,
  GENESIS_TIME,
  calcAccountingReportDataHash,
  getAccountingReportDataItems,
  computeTimestampAtSlot,
  ZERO_HASH,
  CONSENSUS_VERSION,
  computeTimestampAtEpoch,
} = require('../0.8.9/oracle/accounting-oracle-deploy.test')

const getReportFields = (override = {}) => ({
  consensusVersion: CONSENSUS_VERSION,
  numValidators: 10,
  clBalanceGwei: e9(320),
  stakingModuleIdsWithNewlyExitedValidators: [1],
  numExitedValidatorsByStakingModule: [3],
  withdrawalVaultBalance: e18(1),
  elRewardsVaultBalance: e18(2),
  sharesRequestedToBurn: e18(3),
  withdrawalFinalizationBatches: [1],
  simulatedShareRate: e27(1),
  isBunkerMode: true,
  extraDataFormat: 0,
  extraDataHash: ZERO_HASH,
  extraDataItemsCount: 0,
  ...override,
})

const oldGetCurrentEpochId = (timestamp) => {
  return toBN(timestamp)
    .sub(toBN(GENESIS_TIME))
    .div(toBN(SLOTS_PER_EPOCH).mul(toBN(SECONDS_PER_SLOT)))
}

async function deployLegacyOracleWithAccountingOracle({ admin, initialEpoch = 1, lastProcessingRefSlot = 31 }) {
  const legacyOracle = await legacyOracleFactory({ appManager: { address: admin } })
  const { locatorAddr, consensus, oracle, lido } = await deployAccountingOracleSetup(admin, {
    initialEpoch,
    legacyOracleAddrArg: legacyOracle.address,
    getLegacyOracle: () => {
      return legacyOracle
    },
  })
  await legacyOracle.initialize(locatorAddr, consensus.address)
  await initAccountingOracle({ admin, oracle, consensus, shouldMigrateLegacyOracle: false, lastProcessingRefSlot })
  return { legacyOracle, consensus, accountingOracle: oracle, lido }
}

module.exports = {
  deployLegacyOracleWithAccountingOracle,
}

contract('LegacyOracle', ([admin, stranger]) => {
  context('Fresh deploy and puppet methods checks', () => {
    let legacyOracle, accountingOracle, lido
    before('deploy', async () => {
      const deployed = await deployLegacyOracleWithAccountingOracle({ admin })
      legacyOracle = deployed.legacyOracle
      accountingOracle = deployed.accountingOracle
      lido = deployed.lido
    })

    it('initial state is correct', async () => {
      assert.equals(await legacyOracle.getVersion(), 4)
      assert.equals(await legacyOracle.getAccountingOracle(), accountingOracle.address)
      assert.equals(await legacyOracle.getLido(), lido.address)
      const spec = await legacyOracle.getBeaconSpec()
      assert.equals(spec.epochsPerFrame, EPOCHS_PER_FRAME)
      assert.equals(spec.slotsPerEpoch, SLOTS_PER_EPOCH)
      assert.equals(spec.secondsPerSlot, SECONDS_PER_SLOT)
      assert.equals(spec.genesisTime, GENESIS_TIME)
      assert.equals(await legacyOracle.getLastCompletedEpochId(), 0)
    })

    it('handlePostTokenRebase performs AC, emits event and changes state', async () => {
      await impersonate(ethers.provider, lido.address)
      await assert.reverts(
        legacyOracle.handlePostTokenRebase(1, 2, 3, 4, 5, 6, 7, { from: stranger }),
        'SENDER_NOT_ALLOWED'
      )
      const tx = await legacyOracle.handlePostTokenRebase(1, 2, 3, 4, 5, 6, 7, { from: lido.address, gasPrice: 0 })
      assert.emits(tx, 'PostTotalShares', {
        postTotalPooledEther: 6,
        preTotalPooledEther: 4,
        timeElapsed: 2,
        totalShares: 5,
      })
      const delta = await legacyOracle.getLastCompletedReportDelta()
      assert.equals(delta.postTotalPooledEther, 6)
      assert.equals(delta.preTotalPooledEther, 4)
      assert.equals(delta.timeElapsed, 2)
    })

    it('handleConsensusLayerReport performs AC, emits event and changes state', async () => {
      const refSlot = 3000
      await impersonate(ethers.provider, accountingOracle.address)
      await assert.reverts(
        legacyOracle.handleConsensusLayerReport(refSlot, 2, 3, { from: stranger }),
        'SENDER_NOT_ALLOWED'
      )
      const tx = await legacyOracle.handleConsensusLayerReport(refSlot, 2, 3, {
        from: accountingOracle.address,
        gasPrice: 0,
      })
      const epochId = Math.floor((refSlot + 1) / SLOTS_PER_EPOCH)
      assert.emits(tx, 'Completed', {
        epochId,
        beaconBalance: 2,
        beaconValidators: 3,
      })
      const completedEpoch = await legacyOracle.getLastCompletedEpochId()
      assert.equals(completedEpoch, epochId)
    })
  })

  context('getCurrentEpochId implementation is correct', () => {
    let legacyOracle, consensus, oracle, locatorAddr

    before('deploy time-travelable mock', async () => {
      const implementation = await MockLegacyOracle.new({ from: admin })
      const proxy = await OssifiableProxy.new(implementation.address, admin, '0x')
      legacyOracle = await MockLegacyOracle.at(proxy.address)
      ;({ consensus, oracle, locatorAddr } = await deployAccountingOracleSetup(admin, {
        legacyOracleAddrArg: legacyOracle.address,
        getLegacyOracle: () => {
          return legacyOracle
        },
        dataSubmitter: admin,
      }))
      await legacyOracle.initialize(locatorAddr, consensus.address)
      await initAccountingOracle({
        admin,
        oracle,
        consensus,
        shouldMigrateLegacyOracle: false,
        lastProcessingRefSlot: 0,
      })
    })

    it('test', async () => {
      for (let index = 0; index < 20; index++) {
        assert.equals(await legacyOracle.getCurrentEpochId(), oldGetCurrentEpochId(await consensus.getTime()))
        await consensus.advanceTimeByEpochs(1)
      }
    })
  })

  context('Migration from old contract', () => {
    const lastCompletedEpoch = 10
    let oldImplementation
    let newImplementation
    let proxy
    let proxyAsOldImplementation
    let proxyAsNewImplementation
    let deployedInfra

    before('deploy old implementation and set as proxy', async () => {
      oldImplementation = await MockLegacyOracle.new({ from: admin })
      newImplementation = await LegacyOracle.new({ from: admin })
      proxy = await OssifiableProxy.new(oldImplementation.address, admin, '0x')
      proxyAsOldImplementation = await MockLegacyOracle.at(proxy.address)
    })

    it('implementations are petrified', async () => {
      await assert.reverts(oldImplementation.initialize(stranger, stranger), 'INIT_ALREADY_INITIALIZED')
      await assert.reverts(newImplementation.initialize(stranger, stranger), 'INIT_ALREADY_INITIALIZED')
    })

    it('set state to mimic legacy oracle', async () => {
      await proxyAsOldImplementation.initializeAsV3()
      await proxyAsOldImplementation.setParams(
        EPOCHS_PER_FRAME,
        SLOTS_PER_EPOCH,
        SECONDS_PER_SLOT,
        GENESIS_TIME,
        lastCompletedEpoch
      )
    })

    it('deploy&initialize all contracts', async () => {
      deployedInfra = await deployAccountingOracleSetup(admin, {
        legacyOracleAddrArg: proxy.address,
        getLegacyOracle: () => {
          return proxyAsOldImplementation
        },
        dataSubmitter: admin,
      })
      const { consensus, oracle } = deployedInfra
      await initAccountingOracle({ admin, oracle, consensus, shouldMigrateLegacyOracle: true })
    })

    it('upgrade implementation', async () => {
      await proxy.proxy__upgradeTo(newImplementation.address)
      proxyAsNewImplementation = await LegacyOracle.at(proxy.address)
      await proxyAsNewImplementation.finalizeUpgrade_v4(deployedInfra.oracle.address)
    })

    it('submit report', async () => {
      await deployedInfra.consensus.advanceTimeToNextFrameStart()
      const { refSlot } = await deployedInfra.consensus.getCurrentFrame()
      const reportFields = getReportFields({
        refSlot: +refSlot,
      })
      const reportItems = getAccountingReportDataItems(reportFields)
      const reportHash = calcAccountingReportDataHash(reportItems)
      await deployedInfra.consensus.addMember(admin, 1, { from: admin })
      await deployedInfra.consensus.submitReport(refSlot, reportHash, CONSENSUS_VERSION, { from: admin })
      const oracleVersion = +(await deployedInfra.oracle.getContractVersion())
      const tx = await deployedInfra.oracle.submitReportData(reportItems, oracleVersion, { from: admin })

      const epochId = Math.floor((+refSlot + 1) / SLOTS_PER_EPOCH)
      assert.emits(
        tx,
        'Completed',
        {
          epochId,
          beaconBalance: web3.utils.toWei(reportFields.clBalanceGwei, 'gwei'),
          beaconValidators: reportFields.numValidators,
        },
        { abi: LegacyOracleAbi }
      )
      const completedEpoch = await proxyAsNewImplementation.getLastCompletedEpochId()
      assert.equals(completedEpoch, epochId)
    })

    it('time in sync with consensus', async () => {
      await deployedInfra.consensus.advanceTimeToNextFrameStart()
      const { frameEpochId, frameStartTime, frameEndTime } = await proxyAsNewImplementation.getCurrentFrame()
      const consensusFrame = await deployedInfra.consensus.getCurrentFrame()
      const refSlot = consensusFrame.refSlot.toNumber()
      assert.equals(frameEpochId, Math.floor((refSlot + 1) / SLOTS_PER_EPOCH))
      assert.equals(frameStartTime, computeTimestampAtSlot(refSlot + 1))
      assert.equals(frameEndTime, computeTimestampAtEpoch(+frameEpochId + EPOCHS_PER_FRAME) - 1)
    })

    it.skip('handlePostTokenRebase from lido')
  })
})
