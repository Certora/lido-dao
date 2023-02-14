const { BN } = require('bn.js')
const { assert } = require('../../helpers/assert')
const { assertBn, assertEvent, assertAmountOfEvents } = require('@aragon/contract-helpers-test/src/asserts')
const { assertRevert } = require('../../helpers/assertThrow')
const { e9, e18, e27, hex, printEvents } = require('../../helpers/utils')
const { ZERO_ADDRESS, bn } = require('@aragon/contract-helpers-test')

const {
  SLOTS_PER_EPOCH, SECONDS_PER_SLOT, GENESIS_TIME, SECONDS_PER_EPOCH,
  EPOCHS_PER_FRAME, SLOTS_PER_FRAME, SECONDS_PER_FRAME,
  computeSlotAt, computeEpochAt, computeEpochFirstSlotAt,
  computeEpochFirstSlot, computeTimestampAtSlot, computeTimestampAtEpoch,
  ZERO_HASH, CONSENSUS_VERSION,
  V1_ORACLE_LAST_REPORT_SLOT,
  EXTRA_DATA_FORMAT_LIST, EXTRA_DATA_TYPE_STUCK_VALIDATORS, EXTRA_DATA_TYPE_EXITED_VALIDATORS,
  deployAndConfigureAccountingOracle, getReportDataItems, calcReportDataHash, encodeExtraDataItems,
  packExtraDataList, calcExtraDataListHash} = require('./accounting-oracle-deploy.test')


contract('AccountingOracle', ([admin, member1, member2, member3, stranger]) => {

  context('Happy path', () => {
    let consensus
    let oracle
    let oracleVersion
    let mockLido
    let mockWithdrawalQueue
    let mockStakingRouter
    let mockLegacyOracle

    let extraData
    let extraDataItems
    let extraDataList
    let extraDataHash
    let reportFields
    let reportItems
    let reportHash

    before(async () => {
      const deployed = await deployAndConfigureAccountingOracle(admin)
      consensus = deployed.consensus
      oracle = deployed.oracle
      mockLido = deployed.lido
      mockWithdrawalQueue = deployed.withdrawalQueue
      mockStakingRouter = deployed.stakingRouter
      mockLegacyOracle = deployed.legacyOracle

      oracleVersion = +await oracle.getContractVersion()

      await consensus.addMember(member1, 1, {from: admin})
      await consensus.addMember(member2, 2, {from: admin})
      await consensus.addMember(member3, 2, {from: admin})

      await consensus.advanceTimeBySlots(SECONDS_PER_EPOCH + 1)
    })

    async function triggerConsensusOnHash(hash) {
      const {refSlot} = await consensus.getCurrentFrame()
      await consensus.submitReport(refSlot, hash, CONSENSUS_VERSION, { from: member1 })
      await consensus.submitReport(refSlot, hash, CONSENSUS_VERSION, { from: member3 })
      assert.equal((await consensus.getConsensusState()).consensusReport, hash)
    }

    it('initially, consensus report is empty and is not being processed', async () => {
      const report = await oracle.getConsensusReport()
      assert.equal(report.hash, ZERO_HASH)
      // see the next test for refSlot
      assert.equal(+report.processingDeadlineTime, 0)
      assert.isFalse(report.processingStarted)

      const frame = await consensus.getCurrentFrame()
      const procState = await oracle.getProcessingState()

      assert.equal(+procState.currentFrameRefSlot, +frame.refSlot)
      assert.equal(+procState.processingDeadlineTime, 0)
      assert.equal(procState.mainDataHash, ZERO_HASH)
      assert.isFalse(procState.mainDataSubmitted)
      assert.equal(procState.extraDataHash, ZERO_HASH)
      assert.equal(+procState.extraDataFormat, 0)
      assert.equal(+procState.extraDataItemsCount, 0)
      assert.equal(+procState.extraDataItemsSubmitted, 0)
    })

    it(`reference slot of the empty initial consensus report is set to the last processed slot ` +
       `of the legacy oracle`, async () =>
    {
      const report = await oracle.getConsensusReport()
      assert.equal(+report.refSlot, V1_ORACLE_LAST_REPORT_SLOT)
    })

    it('committee reaches consensus on a report hash', async () => {
      const {refSlot} = await consensus.getCurrentFrame()

      extraData = {
        stuckKeys: [
          {moduleId: 1, nodeOpIds: [0], keysCounts: [1]},
          {moduleId: 2, nodeOpIds: [0], keysCounts: [2]},
          {moduleId: 3, nodeOpIds: [2], keysCounts: [3]},
        ],
        exitedKeys: [
          {moduleId: 2, nodeOpIds: [1, 2], keysCounts: [1, 3]},
          {moduleId: 3, nodeOpIds: [1], keysCounts: [2]},
        ],
      }

      extraDataItems = encodeExtraDataItems(extraData)
      extraDataList = packExtraDataList(extraDataItems)
      extraDataHash = calcExtraDataListHash(extraDataList)

      reportFields = {
        consensusVersion: CONSENSUS_VERSION,
        refSlot: +refSlot,
        numValidators: 10,
        clBalanceGwei: e9(320),
        stakingModuleIdsWithNewlyExitedValidators: [1],
        numExitedValidatorsByStakingModule: [3],
        withdrawalVaultBalance: e18(1),
        elRewardsVaultBalance: e18(2),
        lastWithdrawalRequestIdToFinalize: 1,
        finalizationShareRate: e27(1),
        isBunkerMode: true,
        extraDataFormat: EXTRA_DATA_FORMAT_LIST,
        extraDataHash: extraDataHash,
        extraDataItemsCount: extraDataItems.length,
      }

      reportItems = getReportDataItems(reportFields)
      reportHash = calcReportDataHash(reportItems)

      await triggerConsensusOnHash(reportHash)
    })

    it('oracle gets the report hash', async () => {
      const report = await oracle.getConsensusReport()
      assert.equal(report.hash, reportHash)
      assert.equal(+report.refSlot, +reportFields.refSlot)
      assert.equal(
        +report.processingDeadlineTime,
        computeTimestampAtSlot(+report.refSlot + SLOTS_PER_FRAME)
      )
      assert.isFalse(report.processingStarted)

      const frame = await consensus.getCurrentFrame()
      const procState = await oracle.getProcessingState()

      assert.equal(+procState.currentFrameRefSlot, +frame.refSlot)
      assert.equal(
        +procState.processingDeadlineTime,
        computeTimestampAtSlot(+frame.reportProcessingDeadlineSlot)
      )
      assert.equal(procState.mainDataHash, reportHash)
      assert.isFalse(procState.mainDataSubmitted)
      assert.equal(procState.extraDataHash, ZERO_HASH)
      assert.equal(+procState.extraDataFormat, 0)
      assert.equal(+procState.extraDataItemsCount, 0)
      assert.equal(+procState.extraDataItemsSubmitted, 0)
    })

    it('some time passes', async () => {
      await consensus.advanceTimeBy(Math.floor(SECONDS_PER_FRAME / 3))
    })

    it('non-member cannot submit the data', async () => {
      await assertRevert(
        oracle.submitReportData(reportItems, oracleVersion, {from: stranger}),
        'SenderNotAllowed()'
      )
    })

    it('the data cannot be submitted passing a different contract version', async () => {
      await assertRevert(
        oracle.submitReportData(reportItems, oracleVersion - 1, {from: member1}),
        `UnexpectedContractVersion(${oracleVersion}, ${oracleVersion - 1})`
      )
    })

    it(`a data not matching the consensus hash cannot be submitted`, async () => {
      const invalidReport = { ...reportFields, numValidators: reportFields.numValidators + 1 }
      const invalidReportItems = getReportDataItems(invalidReport)
      const invalidReportHash = calcReportDataHash(invalidReportItems)
      await assertRevert(
        oracle.submitReportData(invalidReportItems, oracleVersion, {from: member1}),
        `UnexpectedDataHash("${reportHash}", "${invalidReportHash}")`
      )
    })

    let prevProcessingRefSlot

    it(`a committee member submits the rebase data`, async () => {
      prevProcessingRefSlot = +await oracle.getLastProcessingRefSlot()
      const tx = await oracle.submitReportData(reportItems, oracleVersion, {from: member1})
      assertEvent(tx, 'ProcessingStarted', {expectedArgs: {refSlot: reportFields.refSlot}})
      assert.isTrue((await oracle.getConsensusReport()).processingStarted)
      assert.isAbove(+await oracle.getLastProcessingRefSlot(), prevProcessingRefSlot)
    })

    it(`extra data processing is started`, async () => {
      const frame = await consensus.getCurrentFrame()
      const procState = await oracle.getProcessingState()

      assert.equal(+procState.currentFrameRefSlot, +frame.refSlot)
      assert.equal(
        +procState.processingDeadlineTime,
        computeTimestampAtSlot(+frame.reportProcessingDeadlineSlot)
      )
      assert.equal(procState.mainDataHash, reportHash)
      assert.isTrue(procState.mainDataSubmitted)
      assert.equal(procState.extraDataHash, reportFields.extraDataHash)
      assert.equal(+procState.extraDataFormat, reportFields.extraDataFormat)
      assert.equal(+procState.extraDataItemsCount, reportFields.extraDataItemsCount)
      assert.equal(+procState.extraDataItemsSubmitted, 0)
    })

    it(`Lido got the oracle report`, async () => {
      const lastOracleReportCall = await mockLido.getLastCall_handleOracleReport()
      assert.equal(lastOracleReportCall.callCount, 1)
      assert.equal(
        +lastOracleReportCall.secondsElapsedSinceLastReport,
        (reportFields.refSlot - V1_ORACLE_LAST_REPORT_SLOT) * SECONDS_PER_SLOT
      )
      assert.equal(+lastOracleReportCall.numValidators, reportFields.numValidators)
      assertBn(lastOracleReportCall.clBalance, e9(reportFields.clBalanceGwei))
      assertBn(lastOracleReportCall.withdrawalVaultBalance, reportFields.withdrawalVaultBalance)
      assertBn(lastOracleReportCall.elRewardsVaultBalance, reportFields.elRewardsVaultBalance)
      assertBn(lastOracleReportCall.lastWithdrawalRequestIdToFinalize, reportFields.lastWithdrawalRequestIdToFinalize)
      assertBn(lastOracleReportCall.finalizationShareRate, reportFields.finalizationShareRate)
      // assert.equal(lastOracleReportCall.isBunkerMode, reportFields.isBunkerMode)
    })

    it(`withdrawal queue got bunker mode report`, async () => {
      const updateBunkerModeLastCall = await mockWithdrawalQueue.lastCall__updateBunkerMode()
      assert.equal(+updateBunkerModeLastCall.callCount, 1)
      assert.equal(+updateBunkerModeLastCall.isBunkerMode, reportFields.isBunkerMode)
      assert.equal(
        +updateBunkerModeLastCall.prevReportTimestamp,
        GENESIS_TIME + prevProcessingRefSlot * SECONDS_PER_SLOT
      )
    })

    it(`Staking router got the exited keys report`, async () => {
      const lastExitedKeysByModuleCall = await mockStakingRouter.lastCall_updateExitedKeysByModule()
      assert.equal(lastExitedKeysByModuleCall.callCount, 1)
      assert.sameOrderedMembers(
        lastExitedKeysByModuleCall.moduleIds.map(x => +x),
        reportFields.stakingModuleIdsWithNewlyExitedValidators
      )
      assert.sameOrderedMembers(
        lastExitedKeysByModuleCall.exitedKeysCounts.map(x => +x),
        reportFields.numExitedValidatorsByStakingModule
      )
    })

    it(`legacy oracle got CL data report`, async () => {
      const lastLegacyOracleCall = await mockLegacyOracle.lastCall__handleConsensusLayerReport()
      assert.equal(+lastLegacyOracleCall.totalCalls, 1)
      assert.equal(+lastLegacyOracleCall.refSlot, reportFields.refSlot)
      assert.equal(+lastLegacyOracleCall.clBalance, e9(reportFields.clBalanceGwei))
      assert.equal(+lastLegacyOracleCall.clValidators, reportFields.numValidators)
    })

    it('some time passes', async () => {
      const deadline = (await oracle.getConsensusReport()).processingDeadlineTime
      await consensus.setTime(deadline)
    })

    it('a non-member cannot submit extra data', async () => {
      await assertRevert(
        oracle.submitReportExtraDataList(extraDataList, {from: stranger}),
        'SenderNotAllowed()'
      )
    })

    it(`an extra data not matching the consensus hash cannot be submitted`, async () => {
      const invalidExtraData = {
        stuckKeys: [ ...extraData.stuckKeys ],
        exitedKeys: [ ...extraData.exitedKeys ],
      }
      invalidExtraData.exitedKeys[0].keysCounts = [...invalidExtraData.exitedKeys[0].keysCounts]
      ++invalidExtraData.exitedKeys[0].keysCounts[0]
      const invalidExtraDataItems = encodeExtraDataItems(invalidExtraData)
      const invalidExtraDataList = packExtraDataList(invalidExtraDataItems)
      const invalidExtraDataHash = calcExtraDataListHash(invalidExtraDataList)
      await assertRevert(
        oracle.submitReportExtraDataList(invalidExtraDataList, {from: member2}),
        `UnexpectedDataHash("${extraDataHash}", "${invalidExtraDataHash}")`
      )
    })

    it('a committee member submits extra data', async () => {
      const tx = await oracle.submitReportExtraDataList(extraDataList, {from: member2})

      assertEvent(tx, 'ExtraDataSubmitted', {expectedArgs: {
        refSlot: reportFields.refSlot,
        itemsProcessed: extraDataItems.length,
        itemsCount: extraDataItems.length,
      }})

      const frame = await consensus.getCurrentFrame()
      const procState = await oracle.getProcessingState()

      assert.equal(+procState.currentFrameRefSlot, +frame.refSlot)
      assert.equal(
        +procState.processingDeadlineTime,
        computeTimestampAtSlot(+frame.reportProcessingDeadlineSlot)
      )
      assert.equal(procState.mainDataHash, reportHash)
      assert.isTrue(procState.mainDataSubmitted)
      assert.equal(procState.extraDataHash, reportFields.extraDataHash)
      assert.equal(+procState.extraDataFormat, reportFields.extraDataFormat)
      assert.equal(+procState.extraDataItemsCount, reportFields.extraDataItemsCount)
      assert.equal(+procState.extraDataItemsSubmitted, extraDataItems.length)
    })

    it('Staking router got the exited keys by node op report', async () => {
      const totalReportCalls = +await mockStakingRouter.totalCalls_reportExitedKeysByNodeOperator()
      assert.equal(totalReportCalls, 2)

      const call1 = await mockStakingRouter.calls_reportExitedKeysByNodeOperator(0)
      assert.equal(+call1.stakingModuleId, 2)
      assert.equal(call1.nodeOperatorIds, '0x' + [1, 2].map(i => hex(i, 8)).join(''))
      assert.equal(call1.keysCounts, '0x' + [1, 3].map(i => hex(i, 16)).join(''))

      const call2 = await mockStakingRouter.calls_reportExitedKeysByNodeOperator(1)
      assert.equal(+call2.stakingModuleId, 3)
      assert.equal(call2.nodeOperatorIds, '0x' + [1].map(i => hex(i, 8)).join(''))
      assert.equal(call2.keysCounts, '0x' + [2].map(i => hex(i, 16)).join(''))
    })

    it('Staking router got the stuck keys by node op report', async () => {
      const totalReportCalls = +await mockStakingRouter.totalCalls_reportStuckKeysByNodeOperator()
      assert.equal(totalReportCalls, 3)

      const call1 = await mockStakingRouter.calls_reportStuckKeysByNodeOperator(0)
      assert.equal(+call1.stakingModuleId, 1)
      assert.equal(call1.nodeOperatorIds, '0x' + [0].map(i => hex(i, 8)).join(''))
      assert.equal(call1.keysCounts, '0x' + [1].map(i => hex(i, 16)).join(''))

      const call2 = await mockStakingRouter.calls_reportStuckKeysByNodeOperator(1)
      assert.equal(+call2.stakingModuleId, 2)
      assert.equal(call2.nodeOperatorIds, '0x' + [0].map(i => hex(i, 8)).join(''))
      assert.equal(call2.keysCounts, '0x' + [2].map(i => hex(i, 16)).join(''))

      const call3 = await mockStakingRouter.calls_reportStuckKeysByNodeOperator(2)
      assert.equal(+call3.stakingModuleId, 3)
      assert.equal(call3.nodeOperatorIds, '0x' + [2].map(i => hex(i, 8)).join(''))
      assert.equal(call3.keysCounts, '0x' + [3].map(i => hex(i, 16)).join(''))
    })
  })
})
