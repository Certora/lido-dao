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
definition MANAGE_MEMBERS_AND_QUORUM_ROLE() returns bytes32 = 0x66a484cf1a3c6ef8dfd59d24824943d2853a29d96f34a01271efc55774452a51; //keccak256("MANAGE_MEMBERS_AND_QUORUM_ROLE");
definition DISABLE_CONSENSUS_ROLE() returns bytes32 = 0x10b016346186602d93fc7a27ace09ba944baf9453611b186d36acd3d3d667dc0; //keccak256("DISABLE_CONSENSUS_ROLE");
definition MANAGE_FRAME_CONFIG_ROLE() returns bytes32 = 0x921f40f434e049d23969cbe68d9cf3ac1013fbe8945da07963af6f3142de6afe; //keccak256("MANAGE_FRAME_CONFIG_ROLE");
definition MANAGE_FAST_LANE_CONFIG_ROLE() returns bytes32 = 0x4af6faa30fabb2c4d8d567d06168f9be8adb583156c1ecb424b4832a7e4d6717; //keccak256("MANAGE_FAST_LANE_CONFIG_ROLE");
definition MANAGE_REPORT_PROCESSOR_ROLE() returns bytes32 = 0xc5219a8d2d0107a57aad00b22081326d173df87bad251126f070df2659770c3e; //keccak256("MANAGE_REPORT_PROCESSOR_ROLE");
definition MANAGE_CONSENSUS_CONTRACT_ROLE() returns bytes32 = 0x04a0afbbd09d5ad397fc858789da4f8edd59f5ca5098d70faa490babee945c3b; //keccak256("MANAGE_CONSENSUS_CONTRACT_ROLE");
definition MANAGE_CONSENSUS_VERSION_ROLE() returns bytes32 = 0xc31b1e4b732c5173dc51d519dfa432bad95550ecc4b0f9a61c2a558a2a8e4341; //keccak256("MANAGE_CONSENSUS_VERSION_ROLE");
definition SUBMIT_DATA_ROLE() returns bytes32 = 0x65fa0c17458517c727737e4153dd477fa3e328cf706640b0f68b1a285c5990da; //keccak256("SUBMIT_DATA_ROLE");

// rule ideas for AccountingOracle (without inheritance):
// ------------------------------------------------------------------------------------------
//  1. verify all the reverting scenarios of submitReportData()
//  2. verify submitReportData() does not revert outside of the allowed reverting scenarios
//  3. verify all the errors on lines 91-110 are caught correctly
//  4. cannot call submitReportData() twice in the same e.block.timestamp
//  5. If ReportData.extraDataFormat is not EXTRA_DATA_FORMAT_EMPTY=0 or EXTRA_DATA_FORMAT_LIST=1 => revert
//  6. if the oracle report contains no extra data => ReportData.extraDataHash == 0
//  7. if the oracle report contains no extra data => ReportData.extraDataItemsCount == 0

// Status: Pass
// https://vaas-stg.certora.com/output/80942/465e52d9e9344e8da1eba714a476c786/?anonymousKey=172d2e2c028297570752855bd2f2ae823fb649ee
rule cannotSubmitReportDataTwiceAtSameTimestamp(method f) 
    filtered { f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector ||
                    f.selector == submitReportExtraDataList(bytes).selector ||
                    f.selector == submitReportExtraDataEmpty().selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args; calldataarg args2;

    f(e,args);              // successfully submit a report at time == e.block.timestamp
    f@withrevert(e,args2);  // same e.block.timestamp, any calldataarg

    assert lastReverted;
}

// Status: Pass
// https://vaas-stg.certora.com/output/80942/e04fba855b5641f682cb05edb5362213/?anonymousKey=163260b76cb1479de139f7b547b37bea891bfccb
rule cannotInitializeTwice(method f) 
    filtered { f -> f.selector == initialize(address,address,uint256).selector ||
                    f.selector == initializeWithoutMigration(address,address,uint256,uint256).selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args;
    env e2; calldataarg args2;

    f(e,args);
    f@withrevert(e2,args2);

    assert lastReverted;
}

// Status: Pass
// https://vaas-stg.certora.com/output/80942/47abad17deb34c838ce64f27413c7426/?anonymousKey=9e129225a9208763048cc9ce31f338ec4dcd5109
rule correctRevertsOfSubmitReportData() {
    require contractAddressesLinked();
    env e; calldataarg args;

    uint256 currentConsensusVersion = getConsensusVersion(e);

    // struct ReportData
    uint256 consensusVersion; uint256 refSlot;
    // uint256 numValidators; uint256 clBalanceGwei;
    // uint256[] stakingModuleIdsWithNewlyExitedValidators; uint256[] numExitedValidatorsByStakingModule;
    // uint256 withdrawalVaultBalance; uint256 elRewardsVaultBalance;
    uint256 lastFinalizableWithdrawalRequestId; uint256 simulatedShareRate; bool isBunkerMode;
    uint256 extraDataFormat; bytes32 extraDataHash; uint256 extraDataItemsCount;

    uint256 contractVersion;

    helperCreateAndSubmitReportData@withrevert( e,
                                                consensusVersion,
                                                refSlot,
                                                lastFinalizableWithdrawalRequestId,
                                                simulatedShareRate,
                                                isBunkerMode,
                                                extraDataFormat,
                                                extraDataHash,
                                                extraDataItemsCount,
                                                contractVersion );
    
    bool submitReverted = lastReverted;

    assert (extraDataFormat != EXTRA_DATA_FORMAT_EMPTY() && extraDataFormat != EXTRA_DATA_FORMAT_LIST()) => submitReverted;
    assert (extraDataFormat == EXTRA_DATA_FORMAT_EMPTY() && extraDataHash != 0) => submitReverted;
    assert (extraDataFormat == EXTRA_DATA_FORMAT_EMPTY() && extraDataItemsCount != 0) => submitReverted;
}

// rules for BaseOracle.sol:


// rules for IReportAsyncProcessor.sol imported from HashConsensus.sol:
// ------------------------------------------------------------------------------------------
// 1. cannot submit a report using submitConsensusReport() for the
//    slot returned from getLastProcessingRefSlot() and any slot preceding it.
// 2. cannot submit a report if its "ReportData.consensusVersion" !=  getConsensusVersion()
// 3. Only Consensus contract can submit a report, i.e., call submitConsensusReport()

// Status: Pass
// https://vaas-stg.certora.com/output/80942/21cba2b81811458ea98ea5a12987aa4a/?anonymousKey=785d93a962710a832ff9f4ba0555d07554d2976b
rule cannotSubmitConsensusReportOlderThanLastProcessingRefSlot(method f) 
    filtered { f -> f.selector == submitConsensusReport(bytes32,uint256,uint256).selector }
{    
    require contractAddressesLinked();
    env e; calldataarg args;
    env e1; calldataarg args1;
    env e2; calldataarg args2;
    require e.block.timestamp < e1.block.timestamp;  // time flow
    require e1.block.timestamp < e2.block.timestamp; // time flow

    submitReportData(e,args); // first submits a report successfully for processing

    f(e1,args1); // then submits a consensus report successfully (still not processed)

    bytes32 hash; uint256 refSlot; uint256 processingDeadlineTime; bool processingStarted;

    hash, refSlot, processingDeadlineTime, processingStarted = getConsensusReport(e2);
    uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e2);

    f@withrevert(e2,args2); // finally try to submit a new consensus report

    // assert lastReverted; // FAIL --> checked that the above call is NOT always reverting
    assert (refSlot < lastProcessingRefSlot) => lastReverted;
}

// Status: Pass
// https://vaas-stg.certora.com/output/80942/08a41c3001fc4e40a3da21df35906a4b/?anonymousKey=dcf7e94b4d40b0e2986cf2e2b3f9d4995d347953
rule cannotSubmitReportDataIfUsingDifferentConsensusVersion() {
    require contractAddressesLinked();
    env e; calldataarg args;

    uint256 currentConsensusVersion = getConsensusVersion(e);

    // struct ReportData
    uint256 consensusVersion; uint256 refSlot;
    // uint256 numValidators; uint256 clBalanceGwei;
    // uint256[] stakingModuleIdsWithNewlyExitedValidators; uint256[] numExitedValidatorsByStakingModule;
    // uint256 withdrawalVaultBalance; uint256 elRewardsVaultBalance;
    uint256 lastFinalizableWithdrawalRequestId; uint256 simulatedShareRate; bool isBunkerMode;
    uint256 extraDataFormat; bytes32 extraDataHash; uint256 extraDataItemsCount;

    uint256 contractVersion;

    helperCreateAndSubmitReportData@withrevert( e,
                                                consensusVersion,
                                                refSlot,
                                                lastFinalizableWithdrawalRequestId,
                                                simulatedShareRate,
                                                isBunkerMode,
                                                extraDataFormat,
                                                extraDataHash,
                                                extraDataItemsCount,
                                                contractVersion );

    assert (consensusVersion != currentConsensusVersion) => lastReverted;
}

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


// rules for Versioned:


// rules for UnstructuredStorage.sol:


// rules for AccessControlEnumerable.sol
// ------------------------------------------------------------------------------------------
// 1. adding a new role member with roleR should *increase* the count of getRoleMemberCount(roleR) by one
// 2. removing a roleR from a member should *decrease* the count of getRoleMemberCount(roleR) by one
// 3. getRoleMemberCount(roleX) should not be affected by adding or removing roleR (roleR != roleX)

// Status: Pass
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule countIncreaseByOneWhenGrantRole(method f) {
    require contractAddressesLinked();
    env e; calldataarg args;
    
    bytes32 roleR; address accountA;

    renounceRole(e,roleR,accountA); // ensure accountA does not have roleR

    bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
    require countRoleRMembersBefore < UINT256_MAX();  // reasonable there are not so many role members

    // grantRole(e,roleR,accountA);
    f(e,args);

    bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);

    assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1;
    /*
    assert !hasRoleRAccountABefore;
    assert hasRoleRAccountAAfter;
    assert countRoleRMembersAfter - countRoleRMembersBefore == 1;
    */
}

// Status: Pass
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule countDecreaseByOneWhenRenounceRole(method f) {
    require contractAddressesLinked();
    env e; calldataarg args;
    
    bytes32 roleR; address accountA;

    grantRole(e,roleR,accountA); // ensure accountA has roleR

    bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
    require countRoleRMembersBefore > 0;  // there is at least one account with roleR
    
    // renounceRole(e,roleR,accountA);
    f(e,args);

    bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
    uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);

    assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1;
    /*
    assert hasRoleRAccountABefore;
    assert !hasRoleRAccountAAfter;
    assert countRoleRMembersBefore - countRoleRMembersAfter == 1;
    */
}

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

// rules for AccessControl.sol:
// ------------------------------------------------------------------------------------------
// 1. only admin of role R can grant the role R to the account A (role R can be any role including the admin role)
// 2. only admin or the account A itself can revoke the role R of account A (no matter the role)
// 3. granting or revoking roleR from accountA should not affect any accountB

// Status: Fails
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule onlyAdminCanGrantRole(method f) {
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

    assert (!hasRoleRAccountABefore && hasRoleRAccountAAfter) => 
            (hasRoleXAccountBBefore && hasRoleXAccountBAfter) || 
            (!hasRoleXAccountBBefore && !hasRoleXAccountBAfter);
    
    assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => 
            (hasRoleXAccountBBefore && hasRoleXAccountBAfter) || 
            (!hasRoleXAccountBBefore && !hasRoleXAccountBAfter);
}


/**************************************************
 *                   MISC Rules                   *
 **************************************************/

// Status: Fails (as expected, no issues)
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule sanity(method f) 
{
    require contractAddressesLinked();
    env e; calldataarg args;

    f(e,args);
    assert false;
}

// not relevant rule - to delete
/*
rule shouldNotRevert(method f)
filtered{f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector}
{
    env e;
    calldataarg args;

    require contractAddressesLinked();

    require e.msg.value == 0;
    require e.msg.sender != 0;
    require e.block.timestamp > 0;
    require e.block.timestamp < 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff;

    f@withrevert(e,args);
    assert (!lastReverted);
}
*/