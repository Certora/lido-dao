import "./StakingRouterBase.spec"
import "./StakingRouterInvariants.spec"

using NodeOperatorsRegistry as NOS
using StakingModuleMock as moduleMock

methods {
    NOS.getStakingModuleSummary() returns (uint256,uint256,uint256) envfree
    NOS.obtainDepositData(uint256, bytes)
    NOS.getActiveNodeOperatorsCount() returns (uint256) envfree
    NOS.getNodeOperatorSummary(uint256) envfree
    moduleMock.getStakingModuleSummary() returns (uint256,uint256,uint256) envfree
}

use invariant modulesCountIsLastIndex
use invariant StakingModuleIdLELast
use invariant StakingModuleIndexIsIdMinus1
use invariant StakingModuleId
use invariant StakingModuleAddressIsNeverZero
use invariant StakingModuleTotalFeeLEMAX
use invariant StakingModuleTargetShareLEMAX
use invariant ZeroAddressForUnRegisteredModule
use invariant ZeroExitedValidatorsForUnRegisteredModule
use invariant StakingModuleAddressIsUnique

definition UINT32_MAX() returns uint32 = 0xFFFFFFFF;
definition UINT64_MAX() returns uint64 = 0xFFFFFFFFFFFFFFFF;

/**************************************************
 *     Staking modules Validators assumptions     *
 **************************************************/
function modulesValidatorsAssumptions() {
    uint256 totalExited1; uint256 totalDeposited1; uint256 totalDepositable1;
    totalExited1, totalDeposited1, totalDepositable1 = NOS.getStakingModuleSummary();
    require totalExited1 <= totalDeposited1;
    require totalDeposited1 <= UINT32_MAX();
    require totalDepositable1 <= UINT64_MAX();

    uint256 totalExited2; uint256 totalDeposited2; uint256 totalDepositable2;
    totalExited2, totalDeposited2, totalDepositable2 = moduleMock.getStakingModuleSummary();
    require totalExited2 <= totalDeposited2;
    require totalDeposited2 <= UINT32_MAX();
    require totalDepositable2 <= UINT64_MAX();
}

function NodeOperatorValidKeys(uint256 nodeOperatorId) {
    bool isTargetLimitActive;
    uint256 targetValidatorsCount;
    uint256 stuckValidatorsCount;
    uint256 refundedValidatorsCount;
    uint256 stuckPenaltyEndTimestamp;
    uint256 totalExitedValidators;
    uint256 totalDepositedValidators;
    uint256 depositableValidatorsCount;

    isTargetLimitActive, targetValidatorsCount, stuckValidatorsCount,
    refundedValidatorsCount, stuckPenaltyEndTimestamp, totalExitedValidators,
    totalDepositedValidators, depositableValidatorsCount = NOS.getNodeOperatorSummary(nodeOperatorId);

    uint256 totalExitedSum; uint256 totalDepositedSum; uint256 totalDepositableSum;
    totalExitedSum, totalDepositedSum, totalDepositableSum = NOS.getStakingModuleSummary();

    require totalExitedSum >= totalExitedValidators;
    require totalDepositedSum >= totalDepositedValidators;
    require totalDepositedValidators >= totalExitedValidators;
    require totalDepositedSum >= totalExitedSum;
}
 
/**************************************************
 *                 MISC Rules                     *
 **************************************************/
rule depositSanity() {
    env e;
    bytes _depositCalldata; require _depositCalldata.length == 32;
    uint256 stakingModuleId;
    uint256 keyCount = 1;
    deposit(e, keyCount, stakingModuleId, _depositCalldata);
    assert false;
}

// The staking modules count can only increase by 1 or not change.
rule stakingModulesCountIncrement(method f) {
    env e;
    calldataarg args;
    uint256 count1 = getStakingModulesCount();
        f(e, args);
    uint256 count2 = getStakingModulesCount();
    assert !isAddModule(f) => count1 == count2;
    assert isAddModule(f) => count2 == count1 + 1;
}

invariant NullStakingModuleStatusIsActive(uint256 id)
    id > getStakingModulesCount() => getStakingModuleIsActive(id)
/**************************************************
 *          Status Definition Rules               *
 **************************************************/
rule moduleStatusDefinition(uint256 moduleId) {
    assert getStakingModuleIsActive(moduleId) <=> 
        getStakingModuleStatus(moduleId) == ACTIVE();

    assert getStakingModuleIsDepositsPaused(moduleId) <=> 
        getStakingModuleStatus(moduleId) == PAUSED();

    assert getStakingModuleIsStopped(moduleId) <=> 
        getStakingModuleStatus(moduleId) == STOPPED();
}

/**************************************************
 *          Status Transition Rules               *
 **************************************************/
rule StatusChangedToActive(uint256 moduleId, method f)
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    require !getStakingModuleIsActive(moduleId);
        
        f(e, args);
    
    assert getStakingModuleIsActive(moduleId) =>
        (f.selector == setStakingModuleStatus(uint256,uint8).selector ||
        f.selector == addStakingModule(string,address,uint256,uint256,uint256).selector ||
        f.selector == resumeStakingModule(uint256).selector);
}

rule StatusChangedToPaused(uint256 moduleId, method f)
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    require !getStakingModuleIsDepositsPaused(moduleId);

        f(e, args);

    assert getStakingModuleIsDepositsPaused(moduleId) =>
        (f.selector == setStakingModuleStatus(uint256,uint8).selector ||
        f.selector == pauseStakingModule(uint256).selector);
}

rule StatusChangedToStopped(uint256 moduleId, method f) 
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    require !getStakingModuleIsStopped(moduleId);
        
        f(e, args);

    assert getStakingModuleIsStopped(moduleId) =>
        (f.selector == setStakingModuleStatus(uint256,uint8).selector);
}

rule oneStatusChangeAtATime(uint256 moduleId, method f) 
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    uint256 otherModule;

    safeAssumptions(otherModule);
    safeAssumptions(moduleId);

    uint8 statusMain_Before = getStakingModuleStatus(moduleId);
    uint8 statusOther_Before = getStakingModuleStatus(otherModule);
        f(e, args);
    uint8 statusMain_After = getStakingModuleStatus(moduleId);
    uint8 statusOther_After = getStakingModuleStatus(otherModule);

    assert (statusMain_Before != statusMain_After && statusOther_Before != statusOther_After)
    => moduleId == otherModule;
}

rule canAddModuleIfNotActive(uint256 id) {
    storage initState = lastStorage;

    env e1; env e2;
    string name;
    address stakingModuleAddress;
    uint256 targetShare;
    uint256 stakingModuleFee;
    uint256 treasuryFee;
    require id > getStakingModulesCount();

    addStakingModule(e1, name, stakingModuleAddress, targetShare, stakingModuleFee, treasuryFee);

    uint8 status; 
    require status == PAUSED() || status == STOPPED();
    setStakingModuleStatus(e2, id, status) at initState;

    addStakingModule@withrevert(e1, name, stakingModuleAddress, targetShare, stakingModuleFee, treasuryFee);
    assert !lastReverted;
}

/**************************************************
 *          Staking module parameters             *
 **************************************************/

rule ExitedValidatorsCountCannotDecrease(method f, uint256 moduleId) 
filtered{f -> !f.isView && !isDeposit(f)} {
    env e;
    calldataarg args;
    safeAssumptions(moduleId);
    uint256 exitedValidators1 = getStakingModuleExitedValidatorsById(moduleId);
        f(e, args);
    uint256 exitedValidators2 = getStakingModuleExitedValidatorsById(moduleId);
    assert exitedValidators2 >= exitedValidators1 ||
        f.selector == unsafeSetExitedValidatorsCount(uint256,uint256,bool,
        (uint256,uint256,uint256,uint256,uint256,uint256)).selector;
}

rule cannotAddStakingModuleIfAlreadyRegistered(uint256 moduleId) {
    env e;
    string name;
    address stakingModuleAddress;
    uint256 targetShare;
    uint256 stakingModuleFee;
    uint256 treasuryFee;
    require moduleId <= getStakingModulesCount();
    addStakingModule(e, name, stakingModuleAddress, targetShare, stakingModuleFee, treasuryFee);
    assert stakingModuleAddress != getStakingModuleAddressById(moduleId);
}

rule aggregatedFeeLT100Percent() {
    
    require getStakingModulesCount() <= 2;
    //safeAssumptions(1);
    //safeAssumptions(getStakingModulesCount());
    requireInvariant StakingModuleTotalFeeLEMAX(1);
    requireInvariant StakingModuleTargetShareLEMAX(1);
    requireInvariant StakingModuleTotalFeeLEMAX(2);
    requireInvariant StakingModuleTargetShareLEMAX(2);
    
    uint96 modulesFee; uint96 treasuryFee; uint256 precision;
    modulesFee, treasuryFee, precision = getStakingFeeAggregateDistribution();
    uint96 totalFee = modulesFee + treasuryFee;

    assert modulesFee <= precision;
    assert treasuryFee <= precision;
    // Relevant when removing the sanity check.
    assert totalFee <= precision;
}

rule validMaxDepositCountBound(uint256 maxDepositsValue) {
    env e;
    uint256 moduleId;
    require getStakingModuleAddressById(moduleId) == NOS;

    uint256 totalExited;
    uint256 totalDeposited;
    uint256 depositable;
    totalExited, totalDeposited, depositable = getStakingModuleSummary(moduleId);

    uint256 maxDepositCount = getStakingModuleMaxDepositsCount(e, moduleId, maxDepositsValue);

    assert maxDepositCount <= depositable;
}
/// The exited keys count never surpasses the summary deposited keys count.
rule moduleActiveValidatorsDoesntUnderflow(method f, uint256 moduleId)
filtered{f -> !f.isView && !isDeposit(f)} {
    //cacheItem.activeValidatorsCount =
    //            totalDepositedValidators -
    //            Math256.max(totalExitedValidators, stakingModuleData.exitedValidatorsCount);
    env e;
    calldataarg args;
    require moduleId > 0;
    require getStakingModulesCount() == 1;
    /// We only care about NodeOperatorsRegistry, since the mock can violate most rules.
    require getStakingModuleAddressById(moduleId) == NOS;
    safeAssumptions(moduleId);

    /// Obtain total module data from summary and Staking Router
    uint256 exitedSummary1;
    uint256 depositedSummary1;
    uint256 depositableSummary1;
    exitedSummary1, depositedSummary1, depositableSummary1 = getStakingModuleSummary(moduleId);
    uint256 exitedModule1 = getStakingModuleExitedValidatorsById(moduleId);
    require exitedSummary1 <= depositedSummary1;
    require exitedModule1 <= depositedSummary1;

    if(isUnSafeUpdate(f)) {
        uint256 _stakingModuleId = moduleId;
        uint256 _nodeOperatorId;
        bool _triggerUpdateFinish;
        SR.ValidatorsCountsCorrection correction;
        NodeOperatorValidKeys(_nodeOperatorId);
        unsafeSetExitedValidatorsCount(e, _stakingModuleId, _nodeOperatorId, _triggerUpdateFinish, correction);
    }
    else{
        f(e, args);
    }
    
    /// Obtain total module data from summary and Staking Router post update:
    uint256 exitedSummary2;
    uint256 depositedSummary2;
    uint256 depositableSummary2;
    exitedSummary2, depositedSummary2, depositableSummary2 = getStakingModuleSummary(moduleId);
    uint256 exitedModule2 = getStakingModuleExitedValidatorsById(moduleId);

    // Assert that no underflow is possible.
    assert exitedSummary2 <= depositedSummary2;
    assert exitedModule2 <= depositedSummary2;
}

rule depositDoesntAlterStakingModules(uint256 moduleId) {
    env e; calldataarg args;

    uint8 status1 = getStakingModuleStatus(moduleId);
    address stakingAddress1 = getStakingModuleAddressById(moduleId);
    uint256 exited1 = getStakingModuleExitedValidatorsById(moduleId);
    uint256 ID1 = getStakingModuleIdById(moduleId);
    uint16 fee1 = getStakingModuleFeeById(moduleId);
    uint16 treasuryFee1 = getStakingModuleTreasuryFeeById(moduleId);
    uint16 targetShare1 = getStakingModuleTargetShareById(moduleId);
    uint256 lastModuleID1 = getLastStakingModuleId();
        deposit(e, args);
    uint8 status2 = getStakingModuleStatus(moduleId);
    address stakingAddress2 = getStakingModuleAddressById(moduleId);
    uint256 exited2 = getStakingModuleExitedValidatorsById(moduleId);
    uint256 ID2 = getStakingModuleIdById(moduleId);
    uint16 fee2 = getStakingModuleFeeById(moduleId);
    uint16 treasuryFee2 = getStakingModuleTreasuryFeeById(moduleId);
    uint16 targetShare2 = getStakingModuleTargetShareById(moduleId);
    uint256 lastModuleID2 = getLastStakingModuleId();

    assert( 
        status1 == status2 &&
        stakingAddress1 == stakingAddress2 &&
        exited1 == exited2 &&
        ID1 == ID2 &&
        fee1 == fee2 &&
        treasuryFee1 == treasuryFee2 &&
        targetShare1 == targetShare2 &&
        lastModuleID1 == lastModuleID2);
}

rule afterDepositSummaryIsUpdatedCorrectly(uint256 moduleId, uint256 depositableEther) {
    env e;

    bytes calldata; require calldata.length == 32;
    require getStakingModuleAddressById(moduleId) == NOS;
    require NOS.getActiveNodeOperatorsCount() <= 3;    
    uint256 depositCount = getStakingModuleMaxDepositsCount(e, moduleId, depositableEther);

    uint256 exited_before; uint256 exited_after;
    uint256 deposited_before; uint256 deposited_after;
    uint256 depositable_before; uint256 depositable_after;
    exited_before, deposited_before, depositable_before = 
        NOS.getStakingModuleSummary();

        NOS.obtainDepositData(e, depositCount, calldata);

    exited_after, deposited_after, depositable_after = 
        NOS.getStakingModuleSummary();

    assert deposited_after == deposited_before + depositCount,
    "The deposited keys count summary was not updated correctly";
}

/**************************************************
 *          Revert Characteristics                *
 **************************************************/

rule feeDistributionDoesntRevertAfterAddingModule() {
    env e;
    require getStakingModulesCount() <= 1;    
    uint256 nextId = to_uint256(getStakingModulesCount()+1);
    safeAssumptions(1);
    safeAssumptions(nextId);
    
    /// call the fee distribution function
    getStakingRewardsDistribution();
    
    /// add a new module
    string name;
    address stakingModuleAddress = moduleMock;
    uint256 targetShare;
    uint256 stakingModuleFee;
    uint256 treasuryFee;
    addStakingModule(e, name, stakingModuleAddress, targetShare, stakingModuleFee, treasuryFee);
          
    /// Probe the validators summary for the newly added module
    /// as to assume that the validators state in that module is valid.
    modulesValidatorsAssumptions();
    
    // call again to the fee distribution
    getStakingRewardsDistribution@withrevert();

    assert !lastReverted;
}

rule canAlwaysAddAnotherStakingModule() {
    env e;
    string name1;
    address Address1;
    uint256 targetShare1;
    uint256 ModuleFee1;
    uint256 TreasuryFee1;

    string name2;
    address Address2;
    uint256 targetShare2;
    uint256 ModuleFee2;
    uint256 TreasuryFee2;

    safeAssumptions(getStakingModulesCount());
    // Assuming we don't reach the total cap of staking modules in the contract.
    require getStakingModulesCount() < 30;

    // Without this require, the second call would revert, as it's impossible 
    // to add a staking module whose address is already registered.
    require Address1 != Address2;

    storage initState = lastStorage;

    addStakingModule(e, name1, Address1, targetShare1, ModuleFee1, TreasuryFee1);

    addStakingModule(e, name2, Address2, targetShare2, ModuleFee2, TreasuryFee2) at initState;
    
    // This function fetches the `name` attribute of the next struct in the mapping
    // to make sure there was a valid storage state before calling the addStakingModule function
    // and writing to that storage slot.
    getStakingModuleNameLengthByIndex(getStakingModulesCount());

    addStakingModule@withrevert(e, name1, Address1, targetShare1, ModuleFee1, TreasuryFee1);

    assert !lastReverted;
}
 
rule cannotInitializeTwice(method f) 
filtered{f-> !isDeposit(f) && f.selector != initialize(address,address,bytes32).selector} {
    env e1;
    env e2;
    env e3;
    calldataarg args1;
    calldataarg args2;
    calldataarg args3;
    initialize(e1, args1);
    f(e3, args3);
    initialize@withrevert(e2, args2);
    assert lastReverted;
}

// This rule only checks that the last one added can be fetched (and doesn't revert).
rule canAlwaysGetAddedStakingModule() {
    env e1;
    env e2;
    require e2.msg.value == 0;
    calldataarg args;
    uint256 id = getStakingModulesCount() + 1;
    requireInvariant modulesCountIsLastIndex();
    addStakingModule(e1, args);

    getStakingModule@withrevert(e2, id);
    assert !lastReverted;
}

rule getMaxDepositsCountRevert_init(uint256 id) {
    env e;

    requireInvariant modulesCountIsLastIndex();
    // Post contructor state
    uint256 maxDepositsValue;
    require getStakingModuleIndexOneBased(id) == 0;
    getStakingModuleMaxDepositsCount@withrevert(e, id, maxDepositsValue);
    assert lastReverted;
}

rule getMaxDepositsCountRevert_preserve(method f, uint256 moduleId, uint256 maxDepositsValue) 
filtered{f -> !isDeposit(f) && !f.isView} {
    env e;
    calldataarg args;

    require (moduleId <= getStakingModulesCount() && moduleId != 0);
    require maxDepositsValue > 0 ;
    safeAssumptions(moduleId);
    require getStakingModuleAddressById(1) == NOS;
    require getStakingModulesCount() == 1;
    modulesValidatorsAssumptions();

    getStakingModuleMaxDepositsCount(e, moduleId, maxDepositsValue);
    getStakingModuleStatus(moduleId);

    f(e, args);

    modulesValidatorsAssumptions();

    getStakingModuleMaxDepositsCount@withrevert(e, moduleId, maxDepositsValue);
    assert !lastReverted;
}

rule reportStakingModuleExitedDoesntRevert(method f, uint256 moduleId) 
filtered{f -> !f.isView} {
    env e1;
    env e2;
    calldataarg args;
    bytes nodeOperatorIds;
    bytes exitedValidatorsCounts;
    uint256 maxDepositsValue;

    require moduleId > 0;
    safeAssumptions(moduleId);
    require getStakingModuleAddressById(moduleId) == NOS;

    storage initState = lastStorage;

    reportStakingModuleExitedValidatorsCountByNodeOperator(
        e1, moduleId, nodeOperatorIds, exitedValidatorsCounts);
    getStakingModuleStatus(moduleId);

    f(e2, args) at initState;

    reportStakingModuleExitedValidatorsCountByNodeOperator@withrevert(
        e1, moduleId, nodeOperatorIds, exitedValidatorsCounts);
    assert !lastReverted;
}

rule whichFunctionsRevertIfStatusIsNotActive(method f, uint256 moduleId) {
    storage initState = lastStorage;

    env e1; 
    env e2;
    calldataarg args;

    // Call any function without reverting
    f(e1, args);
    require getStakingModuleAddressById(moduleId) == NOS;
    safeAssumptions(moduleId);

    // Return to initial storage and change some moduleId status to not active.
    uint8 status; 
    require status == PAUSED() || status == STOPPED();
    setStakingModuleStatus(e2, moduleId, status) at initState;
    // Call again the same function with same arguments that now reverts.
    f@withrevert(e1, args);

    assert lastReverted =>
        (isDeposit(f) || 
        f.selector == setStakingModuleStatus(uint256,uint8).selector ||
        f.selector == resumeStakingModule(uint256).selector ||
        f.selector == pauseStakingModule(uint256).selector);
}

rule rolesChange(method f, bytes32 role, address sender) 
filtered{f -> !f.isView && !isInitialize(f)} {
    env e;
    calldataarg args;

    bool has_role_before = hasRole(role, sender);
        f(e, args);
    bool has_role_after = hasRole(role, sender);
    
    assert has_role_before != has_role_after => roleChangingMethods(f);
}
