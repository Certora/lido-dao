using MockConsensusContract as ConsensusContract
using AccountingOracle as AccountingOracleContract
using StakingRouter as StakingRouterContract
// using LidoLocator as LidoLocatorContract
using OracleReportSanityChecker as OracleReportSanityCheckerContract
using MockLidoForAccountingOracle as LidoContract
using MockWithdrawalQueueForAccountingOracle as WithdrawalQueueContract
using StakingModuleMock as StakingModuleContract
using LegacyOracle as LegacyOracleContract

/**************************************************
 *               Methods Declaration              *
 **************************************************/
methods {
    LIDO() returns (address) envfree
    LOCATOR() returns (address) envfree
    LEGACY_ORACLE() returns (address) envfree

    EXTRA_DATA_FORMAT_EMPTY() returns (uint256) envfree
    EXTRA_DATA_FORMAT_LIST() returns (uint256) envfree

    // IConsensusContract = MockConsensusContract.sol
    getChainConfig() returns (uint256, uint256, uint256) => DISPATCHER(true)
    getCurrentFrame() returns (uint256, uint256) => DISPATCHER(true)
    getIsMember(address) returns (bool) => DISPATCHER(true)
    getFrameConfig() returns (uint256, uint256) => DISPATCHER(true)

    // Locator = LidoLocator.sol
    stakingRouter() returns(address) => NONDET
    oracleReportSanityChecker() returns(address) => NONDET
    withdrawalQueue() returns(address) => NONDET

    // StakingRouter = StakingRouter.sol
    reportStakingModuleExitedValidatorsCountByNodeOperator(uint256, bytes, bytes) => DISPATCHER(true)
    reportStakingModuleStuckValidatorsCountByNodeOperator(uint256, bytes, bytes) => DISPATCHER(true)
    onValidatorsCountsByNodeOperatorReportingFinished() => DISPATCHER(true)
    getExitedValidatorsCountAcrossAllModules() returns (uint256) => DISPATCHER(true)
    updateExitedValidatorsCountByStakingModule(uint256[], uint256[]) => DISPATCHER(true)

    // OracleReportSanityChecker = OracleReportSanityChecker.sol
    checkNodeOperatorsPerExtraDataItemCount(uint256, uint256) => DISPATCHER(true)
    checkAccountingExtraDataListItemsCount(uint256) => DISPATCHER(true)
    checkExitedValidatorsRatePerDay(uint256) => DISPATCHER(true)

    // LegacyOracle = MockLegacyOracle.sol
    getBeaconSpec() returns (uint64, uint64, uint64, uint64) => DISPATCHER(true) // might be able to simplify, only used for one check
    getLastCompletedEpochId() returns (uint256) => DISPATCHER(true)
    handleConsensusLayerReport(uint256, uint256, uint256) => DISPATCHER(true)
    getConsensusContract() returns (address) => DISPATCHER(true) //getConsensusContractCVL()
    getAccountingOracle() returns (address) => DISPATCHER(true) //getAccountingOracleContractCVL()

    // WithdrawalQueue = WithdrawalQueue.sol
    updateBunkerMode(bool, uint256) => DISPATCHER(true)

    // Lido = MockLidoForAccountingOracle.sol
    handleOracleReport(uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)

    // StakingModule = StakingModuleMock.sol
    getStakingModuleSummary() returns (uint256, uint256, uint256) => DISPATCHER(true)
    onExitedAndStuckValidatorsCountsUpdated() => DISPATCHER(true)
    updateExitedValidatorsCount(bytes, bytes) => DISPATCHER(true)
    updateStuckValidatorsCount(bytes, bytes) => DISPATCHER(true)
}

/**************************************************
 *                CVL FUNCS & DEFS                *
 **************************************************/
function getAccountingOracleContractCVL() returns address {
    return currentContract;
}

function getConsensusContractCVL() returns address {
    return ConsensusContract;
}

// this function if required to be TRUE, ensures correct contract linking
function contractAddressesLinked() returns bool {
    env e0;
    address consensusContractAddress = getConsensusContract(e0);
    address accountingOracleAddress = LegacyOracleContract.getAccountingOracle(e0);
    
    return  (consensusContractAddress == ConsensusContract) &&
            (accountingOracleAddress == AccountingOracleContract);
}

definition UINT64_MAX() returns uint64 = 0xFFFFFFFFFFFFFFFF;
definition UINT256_MAX() returns uint256 = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff;

definition DEFAULT_ADMIN_ROLE() returns bytes32 = 0x00;
//definition MANAGE_MEMBERS_AND_QUORUM_ROLE() returns bytes32 = 0x66a484cf1a3c6ef8dfd59d24824943d2853a29d96f34a01271efc55774452a51; //keccak256("MANAGE_MEMBERS_AND_QUORUM_ROLE");
//definition DISABLE_CONSENSUS_ROLE() returns bytes32 = 0x10b016346186602d93fc7a27ace09ba944baf9453611b186d36acd3d3d667dc0; //keccak256("DISABLE_CONSENSUS_ROLE");
//definition MANAGE_FRAME_CONFIG_ROLE() returns bytes32 = 0x921f40f434e049d23969cbe68d9cf3ac1013fbe8945da07963af6f3142de6afe; //keccak256("MANAGE_FRAME_CONFIG_ROLE");
//definition MANAGE_FAST_LANE_CONFIG_ROLE() returns bytes32 = 0x4af6faa30fabb2c4d8d567d06168f9be8adb583156c1ecb424b4832a7e4d6717; //keccak256("MANAGE_FAST_LANE_CONFIG_ROLE");
//definition MANAGE_REPORT_PROCESSOR_ROLE() returns bytes32 = 0xc5219a8d2d0107a57aad00b22081326d173df87bad251126f070df2659770c3e; //keccak256("MANAGE_REPORT_PROCESSOR_ROLE");
definition MANAGE_CONSENSUS_CONTRACT_ROLE() returns bytes32 = 0x04a0afbbd09d5ad397fc858789da4f8edd59f5ca5098d70faa490babee945c3b; //keccak256("MANAGE_CONSENSUS_CONTRACT_ROLE");
definition MANAGE_CONSENSUS_VERSION_ROLE() returns bytes32 = 0xc31b1e4b732c5173dc51d519dfa432bad95550ecc4b0f9a61c2a558a2a8e4341; //keccak256("MANAGE_CONSENSUS_VERSION_ROLE");
definition SUBMIT_DATA_ROLE() returns bytes32 = 0x65fa0c17458517c727737e4153dd477fa3e328cf706640b0f68b1a285c5990da; //keccak256("SUBMIT_DATA_ROLE");



//  rules for AccountingOracle (without inheritance):
// ------------------------------------------------------------------------------------------
//  external non-view functions: initialize(), initializeWithoutMigration(), submitReportData(),
//                               submitReportExtraDataEmpty(), submitReportExtraDataList()
//  definitions                : SUBMIT_DATA_ROLE
//                               EXTRA_DATA_TYPE_STUCK_VALIDATORS, EXTRA_DATA_TYPE_EXITED_VALIDATORS
//                               EXTRA_DATA_FORMAT_EMPTY, EXTRA_DATA_FORMAT_LIST
//  storage slots (state vars) : EXTRA_DATA_PROCESSING_STATE_POSITION
// 
//  1. Cannot initialize() or initializeWithoutMigration() twice
//  2. Cannot initialize() with empty addresses
//  3. verify all the reverting scenarios of submitReportData():
//     a) The caller is not a member of the oracle committee and doesn't possess the SUBMIT_DATA_ROLE.
//     b) The provided contract version is different from the current one.
//     c) The provided consensus version is different from the expected one.
//     d) The provided reference slot differs from the current consensus frame's one.
//     e) The processing deadline for the current consensus frame is missed.
//     f) The keccak256 hash of the ABI-encoded data is different from the last hash provided by the hash consensus contract.
//     g) The provided data doesn't meet safety checks. (in OracleReportSanityChecker.sol)
//  4. If ReportData.extraDataFormat is not EXTRA_DATA_FORMAT_EMPTY=0 or EXTRA_DATA_FORMAT_LIST=1 => revert
//  5. If the oracle report contains no extra data => ReportData.extraDataHash == 0
//  6. If the oracle report contains extra data => ReportData.extraDataHash != 0
//  7. If the oracle report contains no extra data => ReportData.extraDataItemsCount == 0
//  8. If the oracle report contains extra data => ReportData.extraDataItemsCount != 0
//  9. submitReportData(), submitReportExtraDataList(), submitReportExtraDataEmpty
//     can be called only if msg.sender has the appropriate role SUBMIT_DATA_ROLE (same as 1a)
//     or if the caller is a member of the oracle committee
// 10. Cannot call submitReport[Data/ExtraDataList/ExtraDataEmpty] twice at the same e.block.timestamp
// 11. Cannot submit the same reports (Data/ExtraDataList/Empty) twice
// 12. Cannot call submitReportExtraDataEmpty() if the report submitted with submitReportData()
//     had report.extraDataFormat != EXTRA_DATA_FORMAT_EMPTY()
// 13. Cannot call submitReportExtraDataList() if the report submitted with submitReportData()
//     had report.extraDataFormat != EXTRA_DATA_FORMAT_LIST()
// 14. New: no function, except submitReportData(), can change the value in LAST_PROCESSING_REF_SLOT_POSITION
// 14. If the reportExtraDataEmpty() was processed you cannot submit again the same previous submitReportData()
// 15. If the reportExtraDataList() was processed you cannot submit again the same previous submitReportData()
// 16. If the reportExtraDataEmpty() was processed you cannot submit new ReportData for the same refSlot
// 17. If the reportExtraDataList() was processed you cannot submit new ReportData for the same refSlot
// 18. The processed refSlot can only increase
// 19. Cannot submit a new report if the extraData of the previous report was not supplied
// 20. Cannot submit a new report without calling the submitReportExtraDataEmpty() / submitReportExtraDataList() first
// 21. After successfully processing a consensus report, the LastProcessingRefSlot is updated correctly
// 22. Only newer report, pointing to higher refSlot, can be submitted

//  1. Cannot initialize() or initializeWithoutMigration() twice
// Status: Pass
// https://vaas-stg.certora.com/output/80942/e04fba855b5641f682cb05edb5362213/?anonymousKey=163260b76cb1479de139f7b547b37bea891bfccb
rule cannotInitializeTwice(method f, method g) 
    filtered { f -> f.selector == initialize(address,address,uint256).selector ||
                    f.selector == initializeWithoutMigration(address,address,uint256,uint256).selector,
               g -> g.selector == initialize(address,address,uint256).selector ||
                    g.selector == initializeWithoutMigration(address,address,uint256,uint256).selector}
{    
    require contractAddressesLinked();
    env e; calldataarg args;
    env e2; calldataarg args2;

    f(e,args);
    g@withrevert(e2,args2);

    assert lastReverted;
}

//  2. Cannot initialize() with empty addresses
// Status: Pass
// https://vaas-stg.certora.com/output/80942/f264880cd2dd4d0381fdaa06a5234879/?anonymousKey=511229de14f62dab5a22416abd33943fb8b5e538
// if both directions <=> then status: fail
// https://vaas-stg.certora.com/output/80942/622251a95a63420490af941bc010d4ac/?anonymousKey=ea15d59a3222d319a1c85f86159cc315c4e74695
rule cannotInitializeWithEmptyAddresses() {
    require contractAddressesLinked();
    env e; calldataarg args;
    // require e.msg.value == 0;

    address admin; address consensusContract; uint256 consensusVersion;
    initialize@withrevert(e, admin, consensusContract, consensusVersion);

    assert (admin == 0 || consensusContract == 0) => lastReverted;
}

//  3. verify all the reverting scenarios of submitReportData()
//  4. If ReportData.extraDataFormat is not EXTRA_DATA_FORMAT_EMPTY=0 or EXTRA_DATA_FORMAT_LIST=1 => revert
//  5. If the oracle report contains no extra data => ReportData.extraDataHash == 0
//  6. If the oracle report contains extra data => ReportData.extraDataHash != 0
//  7. If the oracle report contains no extra data => ReportData.extraDataItemsCount == 0
//  8. If the oracle report contains extra data => ReportData.extraDataItemsCount != 0
// Status: Pass
// https://vaas-stg.certora.com/output/80942/bd32307a5a324b2881652d1b2258b601/?anonymousKey=b7d045ddc841e27f4a8eea9a7065d7edc0f3ce26
rule correctRevertsOfSubmitReportData() {
    require contractAddressesLinked();
    env e; calldataarg args;

    bool hasSubmitDataRole = hasRole(e,SUBMIT_DATA_ROLE(),e.msg.sender);
    bool callerIsConsensusMember = isConsensusMember(e,e.msg.sender);

    uint256 currentContractVersion = getContractVersion(e);
    uint256 currentConsensusVersion = getConsensusVersion(e);

    bytes32 currentHash; uint256 currentRefSlot; uint256 currentDeadline; bool processingStarted;
    currentHash, currentRefSlot, currentDeadline, processingStarted = getConsensusReport(e);

    uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e);

    // struct ReportData
    uint256 consensusVersion; uint256 refSlot;
    // uint256 numValidators; uint256 clBalanceGwei;
    // uint256[] stakingModuleIdsWithNewlyExitedValidators; uint256[] numExitedValidatorsByStakingModule;
    // uint256 withdrawalVaultBalance; uint256 elRewardsVaultBalance;
    uint256 lastFinalizableWithdrawalRequestId; uint256 simulatedShareRate; bool isBunkerMode;
    uint256 extraDataFormat; bytes32 extraDataHash; uint256 extraDataItemsCount;

    uint256 contractVersion;

    bytes32 submittedHash = helperCreateAndSubmitReportData@withrevert( e,
                                consensusVersion, refSlot,
                                lastFinalizableWithdrawalRequestId, simulatedShareRate, isBunkerMode,
                                extraDataFormat, extraDataHash, extraDataItemsCount,
                                contractVersion );
    
    bool submitReverted = lastReverted;

    assert (!hasSubmitDataRole && !callerIsConsensusMember) => submitReverted;  // case 3a
    assert (contractVersion != currentContractVersion)      => submitReverted;  // case 3b
    assert (consensusVersion != currentConsensusVersion)    => submitReverted;  // case 3c
    assert (refSlot != currentRefSlot)                      => submitReverted;  // case 3d
    assert (e.block.timestamp > currentDeadline)            => submitReverted;  // case 3e
    assert (submittedHash != currentHash)                   => submitReverted;  // case 3f

    assert (extraDataFormat != EXTRA_DATA_FORMAT_EMPTY() &&
            extraDataFormat != EXTRA_DATA_FORMAT_LIST())    => submitReverted;  // case 4
    
    assert (extraDataFormat == EXTRA_DATA_FORMAT_EMPTY() && 
            extraDataHash != 0)                             => submitReverted;  // case 5
    
    assert (extraDataFormat == EXTRA_DATA_FORMAT_LIST() && 
            extraDataHash == 0)                             => submitReverted;  // case 6
    
    assert (extraDataFormat == EXTRA_DATA_FORMAT_EMPTY() && 
            extraDataItemsCount != 0)                       => submitReverted;  // case 7
    
    assert (extraDataFormat == EXTRA_DATA_FORMAT_LIST() && 
            extraDataItemsCount == 0)                       => submitReverted;  // case 8
}

//  9. submitReportData(), submitReportExtraDataList(), submitReportExtraDataEmpty
//     can be called only if msg.sender has the appropriate role SUBMIT_DATA_ROLE (same as 1a)
//     or if the caller is a member of the oracle committee
// Status: Pass
// https://vaas-stg.certora.com/output/80942/f4905a42c92847038aa32718403b9c8a/?anonymousKey=7bd858eae6586c20777b7c372fa7dec65ce0ed87
rule callerMustHaveSubmitDataRoleOrBeAConsensusMember(method f) 
    filtered { f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector ||
                    f.selector == submitReportExtraDataList(bytes).selector ||
                    f.selector == submitReportExtraDataEmpty().selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args;

    bool hasSubmitDataRole = hasRole(e,SUBMIT_DATA_ROLE(),e.msg.sender);
    bool callerIsConsensusMember = isConsensusMember(e,e.msg.sender);

    f(e,args);

    assert (!hasSubmitDataRole && !callerIsConsensusMember) => lastReverted;
}

// 10. Cannot call submitReport[Data/ExtraDataList/ExtraDataEmpty] twice at the same e.block.timestamp
// Status: Pass
// https://vaas-stg.certora.com/output/80942/a468b233b03f4f8d8382141d1d0a6eb6/?anonymousKey=f2e33c53956a1dea740d260ea93a234b0fdc8af4
rule cannotSubmitReportDataTwiceAtSameTimestamp(method f) 
    filtered { f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector ||
                    f.selector == submitReportExtraDataList(bytes).selector ||
                    f.selector == submitReportExtraDataEmpty().selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args; env e2; calldataarg args2;

    require e.block.timestamp == e2.block.timestamp;

    f(e,args);              // successfully submit a report at time == e.block.timestamp
    f@withrevert(e2,args2); // same e.block.timestamp, any calldataarg (i.e., any report)

    assert lastReverted;
}

// 11. Cannot submit the same reports (Data/ExtraDataList/Empty) twice
// Status: Pass
// https://vaas-stg.certora.com/output/80942/5ec12c1b2b8c4af8bf4cfd1edae6d148/?anonymousKey=a879498440112f8ef21cf466bfbf9579cc4e3002
rule cannotSubmitTheSameReportDataTwice(method f) 
    filtered { f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector ||
                    f.selector == submitReportExtraDataList(bytes).selector ||
                    f.selector == submitReportExtraDataEmpty().selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args; env e2;

    f(e,args);              // successfully submit a report at time == e.block.timestamp
    f@withrevert(e2,args);  // time can be anytime e.2block.timestamp, but the SAME calldataarg (report)

    assert lastReverted;
}

// 12. Cannot call submitReportExtraDataEmpty() if the report submitted with submitReportData()
//     had report.extraDataFormat != EXTRA_DATA_FORMAT_EMPTY()
// Status: Pass without extra asserts
// https://vaas-stg.certora.com/output/80942/3de063e6c4ef4386a703cc69b5193257/?anonymousKey=b886518a1ceaf175b1b3c553e2976d17ea1b6f77
// Status: Timeouts with extra asserts
// https://vaas-stg.certora.com/output/80942/99847ff728e043d99e3c0f3186c07792/?anonymousKey=d0f44d018c52a17dc9111a28655b8174168d9e2d
rule cannotSubmitReportExtraDataEmptyWhenExtraDataIsNotEmpty() {
    require contractAddressesLinked();
    env e; calldataarg args; env e2;

    uint256 consensusVersion; uint256 refSlot;
    uint256 lastFinalizableWithdrawalRequestId; uint256 simulatedShareRate; bool isBunkerMode;
    uint256 extraDataFormat; bytes32 extraDataHash; uint256 extraDataItemsCount;

    uint256 contractVersion;

    bytes32 submittedHash = helperCreateAndSubmitReportData( e,
                                consensusVersion, refSlot,
                                lastFinalizableWithdrawalRequestId, simulatedShareRate, isBunkerMode,
                                extraDataFormat, extraDataHash, extraDataItemsCount,
                                contractVersion );
    
    submitReportExtraDataEmpty@withrevert(e2);

    bool submitReverted = lastReverted;

    assert (extraDataFormat != EXTRA_DATA_FORMAT_EMPTY())   => submitReverted;
    // assert (extraDataItemsCount != 0)                       => submitReverted;  // causes timeout
    // assert (extraDataHash != 0)                             => submitReverted;  // causes timeout
}

// 13. Cannot call submitReportExtraDataList() if the report submitted with submitReportData()
//     had report.extraDataFormat != EXTRA_DATA_FORMAT_LIST()
// Status: Pass
// https://vaas-stg.certora.com/output/80942/c1df39d3d1f0469ab6383267518fc0b9/?anonymousKey=2a9b2bc84f79cd8307c7341583361091fb0b3b0a
rule cannotSubmitReportExtraDataListWhenExtraDataIsEmpty() {
    require contractAddressesLinked();
    env e; calldataarg args; env e2;

    uint256 consensusVersion; uint256 refSlot;
    uint256 lastFinalizableWithdrawalRequestId; uint256 simulatedShareRate; bool isBunkerMode;
    uint256 extraDataFormat; bytes32 extraDataHash; uint256 extraDataItemsCount;

    uint256 contractVersion;

    bytes32 submittedHash = helperCreateAndSubmitReportData( e,
                                consensusVersion, refSlot,
                                lastFinalizableWithdrawalRequestId, simulatedShareRate, isBunkerMode,
                                extraDataFormat, extraDataHash, extraDataItemsCount,
                                contractVersion );
    
    bytes dataItems;
    submitReportExtraDataList@withrevert(e2, dataItems);

    bool submitReverted = lastReverted;

    assert (extraDataFormat != EXTRA_DATA_FORMAT_LIST())    => submitReverted;
    assert (extraDataItemsCount == 0)                       => submitReverted;
    assert (extraDataHash == 0)                             => submitReverted;
}

// 14. New: no function, except submitReportData(), can change the value in LAST_PROCESSING_REF_SLOT_POSITION
// Status: Pass
// https://vaas-stg.certora.com/output/80942/a7bbd21f04d84a688c1c3c5288e1563c/?anonymousKey=0eb3200a4c0c8bec41ba4d76415a7678c51bfd57
rule nobodyCanChangeLastProcessingRefSlotExceptSubmitReportData(method f)
    filtered { f -> f.selector != submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector &&
                    f.selector != helperCreateAndSubmitReportData(uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256,uint256).selector && 
                    f.selector != initialize(address,address,uint256).selector &&
                    f.selector != initializeWithoutMigration(address,address,uint256,uint256).selector }
                    // filtering the calls to submitReportData()
                    // and to initializer functions that cannot be called twice
{
    require contractAddressesLinked();
    env e; calldataarg args; env e2; calldataarg args2; env e3;

    uint256 lastProcessingRefSlotBefore = getLastProcessingRefSlot(e);
        f(e2,args2);
    uint256 lastProcessingRefSlotAfter = getLastProcessingRefSlot(e3);

    assert lastProcessingRefSlotBefore == lastProcessingRefSlotAfter;
}

// 14. Old: If the reportExtraDataEmpty() was processed you cannot submit again the same previous submitReportData()
// Status: Pass 
// https://vaas-stg.certora.com/output/80942/9024662237794b29996f1cccbd33ceb5/?anonymousKey=efb8e3194e19a36b1afee297e8bedf9045d82ee4
rule cannotSubmitSameReportAfterSubmitExtraDataEmpty() {
    require contractAddressesLinked();
    env e; calldataarg args; env e2; env e3;

    submitReportData(e,args);
    submitReportExtraDataEmpty(e2);
    submitReportData@withrevert(e3,args);  // same args (i.e., same report)

    assert lastReverted;
}

// 15. If the reportExtraDataList() was processed you cannot submit again the same previous submitReportData()
// Status: Pass
// https://vaas-stg.certora.com/output/80942/4493b0822e0b40eba098951f808f4582/?anonymousKey=e99cf27e983f10adbead8782445ff631bedbe253
rule cannotSubmitSameReportAfterSubmitExtraDataList() {
    require contractAddressesLinked();
    env e; calldataarg args; env e2; calldataarg args2; env e3;

    submitReportData(e,args);
    submitReportExtraDataList(e2,args2);
    submitReportData@withrevert(e3,args);  // same args (i.e., same report)

    assert lastReverted;
}

// 16. If the reportExtraDataEmpty() was processed you cannot submit new ReportData for the same refSlot
// Status: Pass
// https://vaas-stg.certora.com/output/80942/87383be6d5ee4b01ac17cfa4ea55d492/?anonymousKey=e1f10de81c79c99da99ab16045f7a879591d9d68
rule cannotSubmitNewReportForSameRefSlotAfterSubmitExtraDataEmpty() {
    require contractAddressesLinked();
    env e; env e2; env e3;

    uint256 refSlot; // we use the same refSlot for both reports

    uint256 consensusVersion_1; 
    uint256 lastFinalizableWithdrawalRequestId_1; uint256 simulatedShareRate_1; bool isBunkerMode_1;
    uint256 extraDataFormat_1; bytes32 extraDataHash_1; uint256 extraDataItemsCount_1;
    uint256 contractVersion_1;

    // step 1
    bytes32 submittedHash1 = helperCreateAndSubmitReportData( e,
                                consensusVersion_1, refSlot,
                                lastFinalizableWithdrawalRequestId_1, simulatedShareRate_1, isBunkerMode_1,
                                extraDataFormat_1, extraDataHash_1, extraDataItemsCount_1,
                                contractVersion_1 );

    // step 2
    submitReportExtraDataEmpty(e2);

    bytes32 reportHash_2; uint256 deadline_2;
    // step 3
    submitConsensusReport@withrevert(e3,reportHash_2,refSlot,deadline_2); // same refSlot

    assert lastReverted;
}

// 17. If the reportExtraDataList() was processed you cannot submit new ReportData for the same refSlot
// Status: Pass
// https://vaas-stg.certora.com/output/80942/df36aedf6cb54a08b7d797167fd1fc18/?anonymousKey=5a280e0a093566efad2194759d8cd6f80c002c8c
rule cannotSubmitNewReportForSameRefSlotAfterSubmitExtraDataList() {
    require contractAddressesLinked();
    env e; env e2; env e3;

    uint256 refSlot; // we use the same refSlot for both reports

    uint256 consensusVersion_1; 
    uint256 lastFinalizableWithdrawalRequestId_1; uint256 simulatedShareRate_1; bool isBunkerMode_1;
    uint256 extraDataFormat_1; bytes32 extraDataHash_1; uint256 extraDataItemsCount_1;
    uint256 contractVersion_1;

    // step 1
    bytes32 submittedHash1 = helperCreateAndSubmitReportData( e,
                                consensusVersion_1, refSlot,
                                lastFinalizableWithdrawalRequestId_1, simulatedShareRate_1, isBunkerMode_1,
                                extraDataFormat_1, extraDataHash_1, extraDataItemsCount_1,
                                contractVersion_1 );
    
    bytes dataItems;
    // step 2
    submitReportExtraDataList(e2,dataItems);

    bytes32 reportHash_2; uint256 deadline_2;
    // step 3
    submitConsensusReport@withrevert(e3,reportHash_2,refSlot,deadline_2); // same refSlot
    
    assert lastReverted;
}

// 18. The processed refSlot can only increase
// Status: Pass
// https://vaas-stg.certora.com/output/80942/727a22b111d747c2b79ff2f75669e29f/?anonymousKey=9b484f5aef39cbb662af10826b9cef40a32ef38d
rule refSlotIsMonotonicallyIncreasing(method f) 
    filtered { f -> f.selector != initialize(address,address,uint256).selector &&
                    f.selector != initializeWithoutMigration(address,address,uint256,uint256).selector }
    // safe filtering as the above methods can be called only once
{
    require contractAddressesLinked();
    env e; env e2; env e3; calldataarg args2;

    uint256 refSlotBefore = getLastProcessingRefSlot(e);
        f(e2,args2);
    uint256 refSlotAfter = getLastProcessingRefSlot(e3);

    assert refSlotBefore <= refSlotAfter;
}

/* Commented out as it takes more than 1hr to run and timeouts
// 19. Cannot submit a new report if the extraData of the previous report was not supplied
// Status: timeout
// https://vaas-stg.certora.com/output/80942/3a889d72976b4d61994e373a2e47c181/?anonymousKey=ccf7c0003e4775248036d611d14300d14ced3a3e
// https://vaas-stg.certora.com/output/80942/aab9d80ff01d4a2a9d2f45e510c4e09e/?anonymousKey=cc27486e6866298bf0f1981c867af722cbdb3374
rule cannotSubmitNewReportIfExtraDataOfPreviousReportWasNotProvided() {
    require contractAddressesLinked();
    env e; env e2; env e3;

    uint256 consensusVersion_1; uint256 refSlot_1;
    uint256 lastFinalizableWithdrawalRequestId_1; uint256 simulatedShareRate_1; bool isBunkerMode_1;
    uint256 extraDataFormat_1; bytes32 extraDataHash_1; uint256 extraDataItemsCount_1;
    uint256 contractVersion_1;

    // step 1 - submit a report (#1) to AccountingOracle that expects extraData later
    require extraDataFormat_1 == EXTRA_DATA_FORMAT_LIST();
    bytes32 submittedHash1 = helperCreateAndSubmitReportData( e,
                                consensusVersion_1, refSlot_1,
                                lastFinalizableWithdrawalRequestId_1, simulatedShareRate_1, isBunkerMode_1,
                                extraDataFormat_1, extraDataHash_1, extraDataItemsCount_1,
                                contractVersion_1 );
    
    bytes32 reportHash_2; uint256 refSlot_2; uint256 deadline_2;

    // step 2 - submit the next consensus report (#2) to BaseOracle
    submitConsensusReport(e2,reportHash_2,refSlot_2,deadline_2); // same refSlot

    uint256 consensusVersion_2;
    uint256 lastFinalizableWithdrawalRequestId_2; uint256 simulatedShareRate_2; bool isBunkerMode_2;
    uint256 extraDataFormat_2; bytes32 extraDataHash_2; uint256 extraDataItemsCount_2;
    uint256 contractVersion_2;

    // step 3
    // submit the next report (#2) to AccountingOracle without providing the extraData for the previous report (#1)
    bytes32 submittedHash2 = helperCreateAndSubmitReportData@withrevert( e3,
                                consensusVersion_2, refSlot_2,
                                lastFinalizableWithdrawalRequestId_2, simulatedShareRate_2, isBunkerMode_2,
                                extraDataFormat_2, extraDataHash_2, extraDataItemsCount_2,
                                contractVersion_2 );

    assert lastReverted;
}
*/

// 20. Cannot submit a new report without calling the submitReportExtraDataEmpty() / submitReportExtraDataList() first
// Status: Fail - we know that it should fail as there is currently no check that extraData was not submitted
// https://vaas-stg.certora.com/output/80942/3eaa9a099efd4e1fb5b99ab8a4b851ec/?anonymousKey=6acc7a21a75a6c55e103376d7139b40d98fd9753
rule cannotSubmitNewReportIfOldWasNotProcessedFirst() {
    require contractAddressesLinked();
    env e; calldataarg args; env e2; calldataarg args2; env e3; calldataarg args3;

    // step 1 - submit a report (#1) to AccountingOracle
    submitReportData(e,args);

    // step 2 - submit the next consensus report (#2) to BaseOracle
    submitConsensusReport(e2,args2);

    // step 3 - submit the next report (#2) to AccountingOracle
    submitReportData@withrevert(e3,args3);

    assert lastReverted;
}

// 21. After successfully processing a consensus report, the LastProcessingRefSlot is updated correctly
// 22. Only newer report, pointing to higher refSlot, can be submitted
// Status: Pass
// https://vaas-stg.certora.com/output/80942/94ea622344854a4cbb90860bc11607cd/?anonymousKey=3e2feb3f2d205463e0fa314e0a4dc9f8b93d4e4b
rule correctUpdateOfLastProcessingRefSlot() {
    require contractAddressesLinked();
    env e; env e2; env e3;

    uint256 lastProcessingRefSlotBefore = getLastProcessingRefSlot(e);

    // Arguments for the new report that will be submitted:
    uint256 consensusVersion_1; uint256 refSlot_1;
    uint256 lastFinalizableWithdrawalRequestId_1; uint256 simulatedShareRate_1; bool isBunkerMode_1;
    uint256 extraDataFormat_1; bytes32 extraDataHash_1; uint256 extraDataItemsCount_1;
    uint256 contractVersion_1;

    // Submit the new report for processing
    bytes32 submittedHash1 = helperCreateAndSubmitReportData( e2,
                                consensusVersion_1, refSlot_1,
                                lastFinalizableWithdrawalRequestId_1, simulatedShareRate_1, isBunkerMode_1,
                                extraDataFormat_1, extraDataHash_1, extraDataItemsCount_1,
                                contractVersion_1 );

    uint256 lastProcessingRefSlotAfter = getLastProcessingRefSlot(e3);

    assert lastProcessingRefSlotAfter == refSlot_1;                     // rule 21
    assert lastProcessingRefSlotBefore < lastProcessingRefSlotAfter;    // rule 22
}



//  rules for BaseOracle.sol:
// ------------------------------------------------------------------------------------------
//  external non-view functions: setConsensusVersion(), setConsensusContract(),
//                               submitConsensusReport()
//  definitions                : MANAGE_CONSENSUS_CONTRACT_ROLE, MANAGE_CONSENSUS_VERSION_ROLE
//  storage slots (state vars) : CONSENSUS_CONTRACT_POSITION, CONSENSUS_VERSION_POSITION
//                               LAST_PROCESSING_REF_SLOT_POSITION, CONSENSUS_REPORT_POSITION
// 
// 1. setConsensusContract() can be called only if msg.sender has the appropriate role
// 2. setConsensusVersion() can be called only if msg.sender has the appropriate role
// 3. Only Consensus contract can submit a report, i.e., call submitConsensusReport()
// 4. Cannot submitConsensusReport() if its refSlot < prevSubmittedRefSlot
// 5. Cannot submitConsensusReport() if its refSlot <= prevProcessingRefSlot
// 6. Cannot submitConsensusReport() if its deadline <= refSlot
// 7. Cannot submitConsensusReport() if its reportHash == 0

// 1. setConsensusContract() can be called only if msg.sender has the appropriate role
// Status: Pass
// https://vaas-stg.certora.com/output/80942/0e9e4a93a81945f3ac7dfc60d531817c/?anonymousKey=506b7ea379db5fed22a8fbdfc81477bedcf25010
rule onlyManagerCanSetConsensusContract() {
    require contractAddressesLinked();
    env e; calldataarg args;

    bytes32 roleManager = MANAGE_CONSENSUS_CONTRACT_ROLE();
    bool isManager = hasRole(e,roleManager,e.msg.sender);

    bytes32 roleAdmin = getRoleAdmin(e,roleManager);
    bool isAdmin = hasRole(e,roleAdmin,e.msg.sender);

    address newAddress;
    setConsensusContract@withrevert(e,newAddress);

    assert (!isManager && !isAdmin) => lastReverted;
}

// 2. setConsensusVersion() can be called only if msg.sender has the appropriate role
// Status: Pass
// https://vaas-stg.certora.com/output/80942/1dd3d3d2456441e5a4cb474b5f933881/?anonymousKey=250fe9c13081828347aaf5dedd477bb59f467554
rule onlyManagerCanSetConsensusVersion() {
    require contractAddressesLinked();
    env e; calldataarg args;

    bytes32 roleManager = MANAGE_CONSENSUS_VERSION_ROLE();
    bool isManager = hasRole(e,roleManager,e.msg.sender);

    bytes32 roleAdmin = getRoleAdmin(e,roleManager);
    bool isAdmin = hasRole(e,roleAdmin,e.msg.sender);

    uint256 newVersion;
    setConsensusVersion@withrevert(e,newVersion);

    assert (!isManager && !isAdmin) => lastReverted;
}

// 3. Only Consensus contract can submit a report, i.e., call submitConsensusReport()
// Status: Pass
// https://vaas-stg.certora.com/output/80942/12dc1ba7763b43a09054482acefef5e1/?anonymousKey=e3f6b40b6a126e42a5784249629cb5fc700c3cc2
rule onlyConsensusContractCanSubmitConsensusReport(method f) 
    filtered { f -> f.selector == submitConsensusReport(bytes32,uint256,uint256).selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args;

    f@withrevert(e,args);

    assert (e.msg.sender != ConsensusContract) => lastReverted;
}

// 4. Cannot submitConsensusReport() if its refSlot < prevSubmittedRefSlot
// Status: Pass
// https://vaas-stg.certora.com/output/80942/d3493f0f47a544d086086b793689841c/?anonymousKey=e0006776f21a9ac59c4745a93d0a7e854c7c4e9a
// https://vaas-stg.certora.com/output/80942/b8d6dd347968456fb9f4522c7d561be8/?anonymousKey=4c8c63d2955006d785feca93d58e27f0d502183f
rule refSlotCannotDecrease() {    
    require contractAddressesLinked();
    env e; calldataarg args;  

    bytes32 prevSubmittedHash; uint256 prevSubmittedRefSlot;
    uint256 prevSubmittedDeadline; bool processingStarted;
    prevSubmittedHash, prevSubmittedRefSlot, prevSubmittedDeadline, processingStarted = getConsensusReport(e);

    bytes32 reportHash; uint256 refSlot; uint256 deadline;
    submitConsensusReport@withrevert(e, reportHash, refSlot, deadline);

    assert (refSlot < prevSubmittedRefSlot) => lastReverted;
}

// 5. Cannot submitConsensusReport() if its refSlot <= prevProcessingRefSlot
// As mentioned in IReportAsyncProcessor imported from HashConsensus.sol
// Status: Pass
// https://vaas-stg.certora.com/output/80942/ea835481700b428aa37c1b82b1ccac33/?anonymousKey=8f394d9d34b1bda2b007f90b7897952c5400a2f0
rule refSlotMustBeGreaterThanProcessingOne() {    
    require contractAddressesLinked();
    env e; calldataarg args;

    uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e);
    
    bytes32 reportHash; uint256 refSlot; uint256 deadline;
    submitConsensusReport@withrevert(e, reportHash, refSlot, deadline);

    assert (refSlot <= lastProcessingRefSlot) => lastReverted;
}

// 6. Cannot submitConsensusReport() if its deadline <= refSlot
// This rule is WRONG as deadline and refslot have different units!
// Status: Fail
// https://vaas-stg.certora.com/output/80942/8c323c10f71b4dafb6b754ba1a4ec865/?anonymousKey=e4b06b987f42ac8c5f9088aa491740d37b475bde
rule deadlineMustBeAfterRefSlotBaseOracle() {    
    require contractAddressesLinked();
    env e; calldataarg args;
    
    bytes32 reportHash; uint256 refSlot; uint256 deadline;
    submitConsensusReport@withrevert(e,reportHash, refSlot, deadline);

    assert (deadline <= refSlot) => lastReverted;
}

// 7. Cannot submitConsensusReport() if its reportHash == 0
// Status: Fail
// https://vaas-stg.certora.com/output/80942/430b70d788dd453eae3647ac444f9cad/?anonymousKey=9f16b9986826770acb548c758fa681767ed4cabf
rule reportHashCannotBeZero() {    
    require contractAddressesLinked();
    env e; calldataarg args;
    
    bytes32 reportHash; uint256 refSlot; uint256 deadline;
    submitConsensusReport@withrevert(e,reportHash, refSlot, deadline);

    assert (reportHash == 0) => lastReverted;
}



//  rules for AccessControlEnumerable.sol
// ------------------------------------------------------------------------------------------
// 1. adding a new role member with roleR should *increase* the count of getRoleMemberCount(roleR) by one
// 2. removing a roleR from a member should *decrease* the count of getRoleMemberCount(roleR) by one
// 3. getRoleMemberCount(roleX) should not be affected by adding or removing roleR (roleR != roleX)

// 1. adding a new role member with roleR should *increase* the count of getRoleMemberCount(roleR) by one
// Status: Old: Pass
// Old: https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// Status: New: Pass
// New: https://vaas-stg.certora.com/output/80942/3407af04b4844c2c9eb4b7f96f929846/?anonymousKey=8ba5d954259341810fa2c5676001cc22eee4e999
rule countIncreaseByOneWhenGrantRole(/*method f*/) {
    require contractAddressesLinked();
    env e; calldataarg args;
    
    bytes32 roleR; address accountA;

    renounceRole(e,roleR,accountA); // ensure accountA does not have roleR

    bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
    require countRoleRMembersBefore < UINT256_MAX();  // reasonable there are not so many role members

    grantRole(e,roleR,accountA);
    // f(e,args);  //old

    bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);

    assert countRoleRMembersAfter == countRoleRMembersBefore + 1; // new

    //assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1; // old
}

// 2. removing a roleR from a member should *decrease* the count of getRoleMemberCount(roleR) by one
// Status: Old: Pass
// Old: https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// Status: New: Pass
// https://vaas-stg.certora.com/output/80942/fa6bd7a1c03c4e3994b792e50a44ac51/?anonymousKey=e6580b3e50550e85539f57773742057ff99ed81e
rule countDecreaseByOneWhenRenounceRole(/*method f*/) {
    require contractAddressesLinked();
    env e; calldataarg args;
    
    bytes32 roleR; address accountA;

    grantRole(e,roleR,accountA); // ensure accountA has roleR

    bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
    require countRoleRMembersBefore > 0;  // there is at least one account with roleR
    
    renounceRole(e,roleR,accountA); // new
    // f(e,args); // old

    bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);

    assert countRoleRMembersAfter == countRoleRMembersBefore - 1; // new

    //assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1; // old
}

// 3. getRoleMemberCount(roleX) should not be affected by adding or removing roleR (roleR != roleX)
// If a member with roleR was added/removed, the count of members with roleX != roleR should not change
// Status: Pass
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule memberCountNonInterference(method f) {
    require contractAddressesLinked();
    env e; calldataarg args;

    bytes32 roleR; bytes32 roleX;

    uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
    uint256 countRoleXMembersBefore = getRoleMemberCount(e,roleX);

    f(e,args);

    uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);
    uint256 countRoleXMembersAfter = getRoleMemberCount(e,roleX);

    require roleR != roleX;
    
    assert (countRoleRMembersAfter > countRoleRMembersBefore) =>
            countRoleXMembersAfter == countRoleXMembersBefore;

    assert (countRoleRMembersAfter < countRoleRMembersBefore) =>
            countRoleXMembersAfter == countRoleXMembersBefore;
}



//  rules for AccessControl.sol:
// ------------------------------------------------------------------------------------------
// 1. only admin of role R can grant the role R to the account A (role R can be any role including the admin role)
// 2. only admin or the account A itself can revoke the role R of account A (no matter the role)
// 3. granting or revoking roleR from accountA should not affect any accountB

// 1. only admin of role R can grant the role R to the account A (role R can be any role including the admin role)
// Status: Fails only on initialize() and initializeWithoutMigration() which can only be called once, so we can filter them
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// Status: Pass
// https://vaas-stg.certora.com/output/80942/e4baa987a34240d18a2531301e772a53/?anonymousKey=231eba328d8c01c657a6494688b8d9eb1ba1368d
rule onlyAdminCanGrantRole(method f)
    filtered { f -> f.selector != initialize(address,address,uint256).selector &&
                    f.selector != initializeWithoutMigration(address,address,uint256,uint256).selector }
    // safe filtering as the above methods can be called only once
{
    require contractAddressesLinked();
    env e; calldataarg args;

    bytes32 roleR; address accountA;
    bool hasRoleRBefore = hasRole(e,roleR,accountA);

    bytes32 roleRAdmin = getRoleAdmin(e,roleR);
    bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);

    f(e,args);

    bool hasRoleRAfter = hasRole(e,roleR,accountA);

    assert (!hasRoleRBefore && hasRoleRAfter) => (isAdmin); 
}

// 2. only admin or the account A itself can revoke the role R of account A (no matter the role)
// Status: Pass
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule onlyAdminOrSelfCanRevokeRole(method f) {
    require contractAddressesLinked();
    env e; calldataarg args;

    bytes32 roleR; address accountA;
    bool hasRoleRBefore = hasRole(e,roleR,accountA);

    bytes32 roleRAdmin = getRoleAdmin(e,roleR);
    bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);

    f(e,args);

    bool hasRoleRAfter = hasRole(e,roleR,accountA);

    assert (hasRoleRBefore && !hasRoleRAfter) => (isAdmin || e.msg.sender == accountA); 
}

// 3. granting or revoking roleR from accountA should not affect any accountB
// Status: Pass
// Note: had to comment line 315 in BaseOracle.sol (to resolve the getProcessingState() dispatcher problem)
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule nonInterferenceOfRolesAndAccounts(method f) {
    require contractAddressesLinked();
    env e; calldataarg args;

    bytes32 roleR; address accountA;
    bytes32 roleX; address accountB;

    bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
    bool hasRoleXAccountBBefore = hasRole(e,roleX,accountB);

    f(e,args);

    bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
    bool hasRoleXAccountBAfter = hasRole(e,roleX,accountB);

    require (roleR != roleX) && (accountA != accountB);

    assert (!hasRoleRAccountABefore && hasRoleRAccountAAfter) =>                // if roleR was granted to AccountA
                (   (hasRoleXAccountBBefore && hasRoleXAccountBAfter)   ||      // then NO change of RoleX
                   (!hasRoleXAccountBBefore && !hasRoleXAccountBAfter)    );    //      of AccountB
    
    assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) =>                // if roleR was revoked from AccountA
                (   (hasRoleXAccountBBefore && hasRoleXAccountBAfter)   ||      // then NO change of RoleX
                   (!hasRoleXAccountBBefore && !hasRoleXAccountBAfter)     );   //      of AccountB
}



/**************************************************
 *                   MISC Rules                   *
 **************************************************/

// Status: Fails (as expected, no issues)
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule sanity(method f) 
filtered { f -> !f.isView }
{
    require contractAddressesLinked();
    env e; calldataarg args;

    f(e,args);
    assert false;
}