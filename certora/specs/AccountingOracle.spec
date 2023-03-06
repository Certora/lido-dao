using MockConsensusContract as ConsensusContract
using AccountingOracle as AccountingOracleContract
using StakingRouter as StakingRouterContract
using LidoLocator as LidoLocatorContract
using OracleReportSanityChecker as OracleReportSanityCheckerContract
using MockLidoForAccountingOracle as LidoContract
using MockWithdrawalQueueForAccountingOracle as WithdrawalQueueContract
using StakingModuleMock as StakingModuleContract
using LegacyOracle as LegacyOracleContract

/**************************************************
 *                 Methods Declaration            *
 **************************************************/
methods {
    LIDO() returns (address) envfree
    LOCATOR() returns (address) envfree
    LEGACY_ORACLE() returns (address) envfree

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
 *               CVL FUNCS & DEFS                 *
 **************************************************/
function getAccountingOracleContractCVL() returns address {
    return currentContract;
}

function getConsensusContractCVL() returns address {
    return ConsensusContract;
}

function contractAddressesLinked() returns bool {
    env e0;
    address consensusContractAddress = getConsensusContract(e0);
    address accountingOracleAddress = LegacyOracleContract.getAccountingOracle(e0);
    
    return  (consensusContractAddress == ConsensusContract) &&
            (accountingOracleAddress == AccountingOracleContract);
}

definition UINT64_MAX() returns uint64 = 0xFFFFFFFFFFFFFFFF;

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
//  1. verify all the reverting scenarios of submitReportData()
//  2. verify submitReportData() does not revert outside of the allowed reverting scenarios
//  3. verify all the errors on lines 91-110 are caught correctly
//  4. 

// rules for BaseOracle.sol:


// rules for HashConsensus.sol:


// rules for Versioned:


// rules for UnstructuredStorage.sol:


// rules for AccessControlEnumerable.sol
// 1. adding a new role member with roleR should *increase* the count of getRoleMemberCount(roleR) by one
// 2. removing a roleR from a member should *decrease* the count of getRoleMemberCount(roleR) by one
// 3. getRoleMemberCount(roleX) should not be affected by adding or removing roleR (roleR != roleX)

// Status: Fails
// https://vaas-stg.certora.com/output/80942/e3745a088a314903be08788e52212ad1/?anonymousKey=95d5c2ace896353df58e60e5164cad4292bb0ad8
rule correctMemberCount(method f) {
    env e;
    calldataarg args;

    require contractAddressesLinked();

    bytes32 roleR; address accountA;
    bytes32 roleX; address accountB;

    bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
    bool hasRoleXAccountBBefore = hasRole(e,roleX,accountB);
    uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
    uint256 countRoleXMembersBefore = getRoleMemberCount(e,roleX);

    f(e,args);

    bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
    bool hasRoleXAccountBAfter = hasRole(e,roleX,accountB);
    uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);
    uint256 countRoleXMembersAfter = getRoleMemberCount(e,roleX);

    require roleR != roleX;
    
    assert (!hasRoleRAccountABefore && hasRoleRAccountAAfter) => countRoleRMembersAfter - countRoleRMembersBefore == 1;
    assert (!hasRoleRAccountABefore && hasRoleRAccountAAfter) => countRoleXMembersAfter - countRoleXMembersBefore == 0;

    assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1;
    assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleXMembersBefore - countRoleXMembersAfter == 0;

}


// rules for AccessControl.sol:
// 1. only admin of role R can grant the role R to the account A (role R can be any role including the admin role)
// 2. only admin or the account A itself can revoke the role R of account A (no matter the role)
// 3. granting or revoking roleR from accountA should not affect any accountB

// Status: Fails
// https://vaas-stg.certora.com/output/80942/e3745a088a314903be08788e52212ad1/?anonymousKey=95d5c2ace896353df58e60e5164cad4292bb0ad8
rule onlyAdminCanGrantRole(method f) {
    env e;
    calldataarg args;

    require contractAddressesLinked();

    bytes32 roleR; address accountA;
    bool hasRoleRBefore = hasRole(e,roleR,accountA);

    bytes32 roleRAdmin = getRoleAdmin(e,roleR);
    bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);

    f(e,args);

    bool hasRoleRAfter = hasRole(e,roleR,accountA);

    assert (!hasRoleRBefore && hasRoleRAfter) => (isAdmin); 
}

// Status: Pass
// https://vaas-stg.certora.com/output/80942/e3745a088a314903be08788e52212ad1/?anonymousKey=95d5c2ace896353df58e60e5164cad4292bb0ad8
rule onlyAdminOrSelfCanRevokeRole(method f) {
    env e;
    calldataarg args;

    require contractAddressesLinked();

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
// https://vaas-stg.certora.com/output/80942/e3745a088a314903be08788e52212ad1/?anonymousKey=95d5c2ace896353df58e60e5164cad4292bb0ad8
rule nonInterferenceOfRolesAndAccounts(method f) {
    env e;
    calldataarg args;

    require contractAddressesLinked();

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

// rules for Math.sol:


// rules for IReportAsyncProcessor ?

// other ideas/considerations:
// only accountingOracle calls withdrawalQueue.updateBunkerMode?


/**************************************************
 *                 MISC Rules                     *
 **************************************************/

// Status: Fails (as expected, no issues)
// https://vaas-stg.certora.com/output/80942/e3745a088a314903be08788e52212ad1/?anonymousKey=95d5c2ace896353df58e60e5164cad4292bb0ad8
rule sanity(method f) 
{
    env e;
    calldataarg args;

    require contractAddressesLinked();

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