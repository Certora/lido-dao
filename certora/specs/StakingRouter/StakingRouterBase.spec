/**************************************************
 *                 Methods Declaration            *
 **************************************************/
methods {
    // StakingModule
    getType() returns (bytes32) => DISPATCHER(true)
    getStakingModuleSummary() returns(uint256, uint256, uint256) => DISPATCHER(true)
    getNodeOperatorSummary(uint256) => DISPATCHER(true)
    getNonce() returns (uint256) => DISPATCHER(true)
    onRewardsMinted(uint256) => DISPATCHER(true)
    onExitedAndStuckValidatorsCountsUpdated() => DISPATCHER(true)
    updateStuckValidatorsCount(bytes, bytes) => DISPATCHER(true)
    updateExitedValidatorsCount(bytes, bytes) => DISPATCHER(true) 
    updateRefundedValidatorsCount(uint256, uint256) => DISPATCHER(true)
    updateTargetValidatorsLimits(uint256, bool, uint256) => DISPATCHER(true)

    _computeDepositDataRootCertora(bytes,bytes,bytes) returns (bytes32) => NONDET
    ///
    onWithdrawalCredentialsChanged() => DISPATCHER(true)
    unsafeUpdateValidatorsCount(uint256,uint256,uint256) => DISPATCHER(true)
    getNodeOperatorsCount() returns (uint256) => DISPATCHER(true)
    getActiveNodeOperatorsCount() returns (uint256) => DISPATCHER(true)
    getNodeOperatorIsActive(uint256) returns (bool) => DISPATCHER(true)
    getNodeOperatorIds(uint256, uint256) returns (uint256[]) => DISPATCHER(true)

    hasRole(bytes32, address) returns (bool) envfree
    getRoleAdmin(bytes32) returns (bytes32) envfree
    getRoleMember(bytes32, uint256) returns (address) envfree
    getRoleMemberCount(bytes32) returns (uint256) envfree

    // StakingRouter
    getStakingModulesCount() returns (uint256) envfree
    getStakingModuleStatus(uint256) returns (uint8) envfree
    getStakingModuleIsStopped(uint256) returns (bool) envfree
    getStakingModuleIsDepositsPaused(uint256) returns (bool) envfree
    getStakingModuleIsActive(uint256) returns (bool) envfree
    getStakingFeeAggregateDistribution() returns (uint96,uint96,uint256) envfree
    getStakingRewardsDistribution() envfree
    getStakingModuleMaxDepositsCount(uint256, uint256) returns (uint256)
    getStakingModuleSummary(uint256) returns ((uint256, uint256, uint256)) envfree
    getStakingModuleActiveValidatorsCount(uint256) returns (uint256) envfree
    FEE_PRECISION_POINTS() returns (uint256) envfree
    TOTAL_BASIS_POINTS() returns (uint256) envfree

    // StakingRouter harness getters
    getStakingModuleAddressById(uint256) returns (address) envfree
    getStakingModuleExitedValidatorsById(uint256) returns (uint256) envfree
    getStakingModuleIdById(uint256) returns (uint256) envfree
    getLastStakingModuleId() returns (uint24) envfree
    getStakingModuleFeeById(uint256) returns (uint16) envfree
    getStakingModuleTreasuryFeeById(uint256) returns (uint16) envfree
    getStakingModuleTargetShareById(uint256) returns (uint16) envfree
    getStakingModuleNameLengthByIndex(uint256) returns (uint256) envfree
    getStakingModuleIndexOneBased(uint256) returns (uint256) envfree
}

/**************************************************
 *                 Definitions                    *
 **************************************************/
// Methods:
definition isDeposit(method f) returns bool = 
    f.selector == deposit(uint256,uint256,bytes).selector;

definition isAddModule(method f) returns bool = 
    f.selector == addStakingModule(string,address,uint256,uint256,uint256).selector;

definition isInitialize(method f) returns bool = 
    f.selector == initialize(address,address,bytes32).selector;

definition roleChangingMethods(method f) returns bool = 
    f.selector == revokeRole(bytes32,address).selector ||
    f.selector == renounceRole(bytes32,address).selector ||
    f.selector == grantRole(bytes32,address).selector;

// Staking module status constants are based on the code StakingModuleStatus.
definition ACTIVE() returns uint8 = 0; 
definition PAUSED() returns uint8 = 1; 
definition STOPPED() returns uint8 = 2; 

definition harnessGetters(method f) returns bool =
    f.selector == getStakingModuleAddressById(uint256).selector ||
    f.selector == getStakingModuleExitedValidatorsById(uint256).selector ||
    f.selector == getStakingModuleIdById(uint256).selector ||
    f.selector == getLastStakingModuleId().selector ||
    f.selector == getStakingModuleFeeById(uint256).selector ||
    f.selector == getStakingModuleTreasuryFeeById(uint256).selector  ||
    f.selector == getStakingModuleTargetShareById(uint256).selector ||
    f.selector == getStakingModuleNameLengthByIndex(uint256).selector ||
    f.selector == getStakingModuleIndexOneBased(uint256).selector;
