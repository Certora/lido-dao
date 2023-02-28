import "./NodeRegistryMethods.spec"

methods {
    getNodeOperatorsCount() returns (uint256) envfree
    getActiveNodeOperatorsCount() returns (uint256) envfree
    getNodeOperatorIsActive(uint256) returns (bool) envfree
    MAX_NODE_OPERATORS_COUNT() returns (uint256) envfree

    getRewardsDistributionShare(uint256, uint256) returns (uint256, uint256)
    getSummaryTotalExitedValidators() returns (uint256) envfree
    getSummaryTotalDepositedValidators() returns (uint256) envfree
    getSummaryTotalKeyCount() returns (uint256) envfree
    getSummaryMaxValidators() returns (uint256) envfree
    getNodeOperator_stuckValidators(uint256) returns (uint256) envfree
    getNodeOperator_refundedValidators(uint256) returns (uint256) envfree
    getNodeOperator_endTimeStamp(uint256) returns (uint256) envfree
    getNodeOperatorSigningStats_exited(uint256) returns (uint64) envfree
    getNodeOperatorSigningStats_vetted(uint256) returns (uint64) envfree
    getNodeOperatorSigningStats_deposited(uint256) returns (uint64) envfree
    getNodeOperatorSigningStats_total(uint256) returns (uint64) envfree
    getNodeOperatorTargetStats_target(uint256) returns (uint64) envfree
    sumOfExitedKeys() returns (uint256) envfree
    sumOfDepositedKeys() returns (uint256) envfree
    sumOfTotalKeys() returns (uint256) envfree
}

definition UINT64_MAX() returns uint64 = 0xFFFFFFFFFFFFFFFF;

/**************************************************
 *                  Methdos defitions             *
 **************************************************/

definition isFinalizeUpgrade(method f) returns bool = 
    f.selector == finalizeUpgrade_v2(address, bytes32, uint256).selector;

definition isObtainDepData(method f) returns bool = 
    f.selector == obtainDepositData(uint256, bytes).selector;

definition isAddSignKeys(method f) returns bool = 
    f.selector == addSigningKeys(uint256, uint256, bytes, bytes).selector;

definition isInvalidateUnused(method f) returns bool = 
    f.selector == onWithdrawalCredentialsChanged().selector ||
    f.selector == invalidateReadyToDepositKeysRange(uint256,uint256).selector;
/**************************************************
 *                 Invariants Helpers             *
 **************************************************/

// Makes sure that if there are any inactive operators, then the sum of active operators
// is strictly less than the sum of all operators accordingly.
function activeOperatorsSumHelper(uint256 id1, uint256 id2) {
    require (id1 != id2 && !getNodeOperatorIsActive(id1) && !getNodeOperatorIsActive(id2)
    && id1 < getNodeOperatorsCount() && id2 < getNodeOperatorsCount()) => 
        getActiveNodeOperatorsCount() + 2 <= getNodeOperatorsCount();

    require (id1 == id2 && !getNodeOperatorIsActive(id1) && id1 < getNodeOperatorsCount()) =>
        getActiveNodeOperatorsCount() + 1 <= getNodeOperatorsCount();
}

function safeAssumptions_NOS(uint256 nodeOperatorId) {
    requireInvariant NodeOperatorsCountLEMAX();
    requireInvariant ActiveOperatorsLECount();
    requireInvariant SumOfDepositedKeysEqualsSummary();
    requireInvariant SumOfExitedKeysEqualsSummary();
    requireInvariant SumOfTotalKeysEqualsSummary();
    requireInvariant AllModulesAreActiveConsistency(nodeOperatorId);
    requireInvariant ExitedKeysLEDepositedKeys(nodeOperatorId);
    requireInvariant DepositedKeysLEVettedKeys(nodeOperatorId);
    requireInvariant VettedKeysLETotalKeys(nodeOperatorId);
}

/**************************************************
 *                  Invariants                    *
 **************************************************/
invariant NodeOperatorsCountLEMAX()
    getNodeOperatorsCount() <= MAX_NODE_OPERATORS_COUNT()

invariant ActiveOperatorsLECount()
    getActiveNodeOperatorsCount() <= getNodeOperatorsCount()
    {
        preserved {
            requireInvariant NodeOperatorsCountLEMAX();
        }

        preserved activateNodeOperator(uint256 id) with (env e) {
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant AllModulesAreActiveConsistency(id);
        }
    }

invariant AllModulesAreActiveConsistency(uint256 nodeOperatorId)
    (
        (getActiveNodeOperatorsCount() == getNodeOperatorsCount() &&
        nodeOperatorId < getActiveNodeOperatorsCount()) 
        => getNodeOperatorIsActive(nodeOperatorId)
    ) 
    {
        preserved {
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant ActiveOperatorsLECount();
        }

        preserved activateNodeOperator(uint256 id) with (env e) {
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant ActiveOperatorsLECount();
            requireInvariant AllModulesAreActiveConsistency(id); 
            activeOperatorsSumHelper(id, nodeOperatorId);
        }

        preserved deactivateNodeOperator(uint256 id) with (env e) {
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant ActiveOperatorsLECount();
            requireInvariant AllModulesAreActiveConsistency(id);
        }
    }


invariant ExitedKeysLEDepositedKeys(uint256 nodeOperatorId)
    getNodeOperatorSigningStats_exited(nodeOperatorId) <=
    getNodeOperatorSigningStats_deposited(nodeOperatorId)
    {
        preserved{
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant DepositedKeysLEVettedKeys(nodeOperatorId);
        }
    }

invariant DepositedKeysLEVettedKeys(uint256 nodeOperatorId)
    getNodeOperatorSigningStats_deposited(nodeOperatorId) <=
    getNodeOperatorSigningStats_vetted(nodeOperatorId)
    {
        preserved{
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant ExitedKeysLEDepositedKeys(nodeOperatorId);
            requireInvariant VettedKeysLETotalKeys(nodeOperatorId);
        }

        preserved invalidateReadyToDepositKeysRange(uint256 _indexFrom, uint256 _indexTo) with (env e){
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant ExitedKeysLEDepositedKeys(_indexFrom);
            requireInvariant DepositedKeysLEVettedKeys(_indexFrom);
            requireInvariant ExitedKeysLEDepositedKeys(_indexTo);
            requireInvariant DepositedKeysLEVettedKeys(_indexTo);

        }
    }

invariant VettedKeysLETotalKeys(uint256 nodeOperatorId)
    getNodeOperatorSigningStats_vetted(nodeOperatorId) <=
    getNodeOperatorSigningStats_total(nodeOperatorId)
    {
        preserved {
            requireInvariant NodeOperatorsCountLEMAX();
            requireInvariant ExitedKeysLEDepositedKeys(nodeOperatorId);
            requireInvariant DepositedKeysLEVettedKeys(nodeOperatorId);
        }

        preserved invalidateReadyToDepositKeysRange(uint256 _indexFrom, uint256 _indexTo) with (env e){
            safeAssumptions_NOS(_indexFrom);
            safeAssumptions_NOS(_indexTo);
        }
    }

/// See rule #targetPlusExitedDoesntOverflow
invariant TargetPlusExitedDoesntOverflow(uint256 nodeOperatorId)
    getNodeOperatorSigningStats_exited(nodeOperatorId) +
    getNodeOperatorTargetStats_target(nodeOperatorId) <= UINT64_MAX()

invariant SumOfDepositedKeysEqualsSummary()
    sumOfDepositedKeys() == getSummaryTotalDepositedValidators()

invariant SumOfExitedKeysEqualsSummary()
    sumOfExitedKeys() == getSummaryTotalExitedValidators()

invariant SumOfTotalKeysEqualsSummary()
    sumOfTotalKeys() == getSummaryTotalKeyCount()

/**************************************************
 *        Revert characteristics       *
 **************************************************/

 rule canAlwaysDeactivateAddedNodeOperator(method f) 
 filtered{f -> !f.isView && f.selector != deactivateNodeOperator(uint256).selector} {
    env e1;
    env e2;
    calldataarg args;
    require e1.msg.sender == e2.msg.sender;
    require e1.msg.value == e2.msg.value;

    string name; require name.length == 32;
    address rewardAddress;
    uint256 nodeOperatorId = getNodeOperatorsCount();
    safeAssumptions_NOS(nodeOperatorId);
    addNodeOperator(e1, name, rewardAddress);

    f(e2, args);

    requireInvariant TargetPlusExitedDoesntOverflow(nodeOperatorId);

    deactivateNodeOperator@withrevert(e2, nodeOperatorId);
    assert !lastReverted;
 }

 rule canDeactivateAfterActivate(method f, uint256 nodeOperatorId)
 filtered{f -> !f.isView && f.selector != deactivateNodeOperator(uint256).selector} {
    env e1;
    env e2;
    calldataarg args;
    require e1.msg.sender == e2.msg.sender;
    require e1.msg.value == e2.msg.value;

    safeAssumptions_NOS(nodeOperatorId);
    activateNodeOperator(e1, nodeOperatorId);
    
    f(e2, args);

    requireInvariant TargetPlusExitedDoesntOverflow(nodeOperatorId);

    deactivateNodeOperator@withrevert(e2, nodeOperatorId);

    assert !lastReverted;
}

rule canActivateAfterDeactivate(method f, uint256 nodeOperatorId)
filtered{f -> !f.isView && f.selector != activateNodeOperator(uint256).selector
 && !isInvalidateUnused(f)} {
    env e1;
    env e2;
    calldataarg args;
    require e1.msg.sender == e2.msg.sender;
    require e1.msg.value == e2.msg.value;

    safeAssumptions_NOS(nodeOperatorId);
    deactivateNodeOperator(e1, nodeOperatorId);

    f(e2, args);
    
    requireInvariant TargetPlusExitedDoesntOverflow(nodeOperatorId);

    activateNodeOperator@withrevert(e2, nodeOperatorId);

    assert !lastReverted;
}

rule cannotFinalizeUpgradeTwice() {
    env e1;
    env e2;
    calldataarg args1;
    calldataarg args2;
    finalizeUpgrade_v2(e1, args1);
    finalizeUpgrade_v2@withrevert(e2, args2);
    assert lastReverted;
}

rule sumOfRewardsSharesLETotalShares(uint256 totalRewardShares) {
    env e;
    uint256 sumOfShares;
    uint256 _share;

    require getNodeOperatorsCount() > 0;

    sumOfShares, _share = getRewardsDistributionShare(e, totalRewardShares, 0);
    assert sumOfShares <= totalRewardShares;
}

rule rewardSharesAreMonotonicWithTotalShares(
    uint256 nodeOperatorId, 
    uint256 totalRewardShares1, 
    uint256 totalRewardShares2) {

    env e;
    require totalRewardShares2 == totalRewardShares1 + 1;
    //require totalRewardShares2 > totalRewardShares1;
    uint256 sumOfShares1; uint256 sumOfShares2;
    uint256 share1; uint256 share2;

    safeAssumptions_NOS(0);
    safeAssumptions_NOS(1);
    
    sumOfShares1, share1 = getRewardsDistributionShare(e, totalRewardShares1, nodeOperatorId);
    sumOfShares2, share2 = getRewardsDistributionShare(e, totalRewardShares2, nodeOperatorId);

    assert sumOfShares2 >= sumOfShares1;
    assert share2 >= share1;
}

// Check that the penalty of nodeOperatorId is removed.
// Also check that no other node operator changed its penalty status.
rule afterClearPenaltyOperatorIsNotPenalized(uint256 nodeOperatorId) {
    env e1;
    env e2;
    require e1.block.timestamp <= e2.block.timestamp;
    uint256 otherNode; require otherNode != nodeOperatorId;
    bool penalizedOther1 = isOperatorPenalized(e1, otherNode);

    clearNodeOperatorPenalty(e1, nodeOperatorId);
    assert !isOperatorPenalized(e2, nodeOperatorId);

    bool penalizedOther2 = isOperatorPenalized(e1, otherNode);
    assert penalizedOther2 == penalizedOther1;
}

/**************************************************
 *    Node Operator SigningStats change rules     *
**************************************************/

rule exitedKeysDontDecrease(method f, uint256 nodeOperatorId) 
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    
    safeAssumptions_NOS(nodeOperatorId);

    uint256 exited_before = getNodeOperatorSigningStats_exited(nodeOperatorId);
    require exited_before <= to_uint256(1 << 32);
        f(e, args);
    uint256 exited_after = getNodeOperatorSigningStats_exited(nodeOperatorId);
    assert exited_before <= exited_after;
}

rule exitedKeysChangeForOnlyOneNodeOperator(method f, uint256 nodeOperatorId1) 
filtered{f -> isInvalidateUnused(f)} {
    env e;
    calldataarg args;
    uint256 nodeOperatorId2;
    safeAssumptions_NOS(nodeOperatorId1);
    safeAssumptions_NOS(nodeOperatorId2);
    
    uint256 exited_before_1 = getNodeOperatorSigningStats_exited(nodeOperatorId1);
    uint256 exited_before_2 = getNodeOperatorSigningStats_exited(nodeOperatorId2);
        f(e, args);
    uint256 exited_after_1 = getNodeOperatorSigningStats_exited(nodeOperatorId1);
    uint256 exited_after_2 = getNodeOperatorSigningStats_exited(nodeOperatorId2);

    assert (exited_before_1 != exited_after_1 && exited_before_2 != exited_after_2) 
        => (nodeOperatorId1 == nodeOperatorId2 || 
        f.selector == updateExitedValidatorsCount(bytes,bytes).selector);
}

rule depositedKeysDontDecrease(method f, uint256 nodeOperatorId) 
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    uint256 deposited_before = getNodeOperatorSigningStats_deposited(nodeOperatorId);
        f(e, args);
    uint256 deposited_after = getNodeOperatorSigningStats_deposited(nodeOperatorId);
    assert deposited_before <= deposited_after;
}

rule depositedKeysChangeForOnlyOneNodeOperator(method f, uint256 nodeOperatorId1) 
filtered{f -> !f.isView} {
    env e;
    calldataarg args;
    uint256 nodeOperatorId2;
    uint256 deposited_before_1 = getNodeOperatorSigningStats_deposited(nodeOperatorId1);
    uint256 deposited_before_2 = getNodeOperatorSigningStats_deposited(nodeOperatorId2);
        f(e, args);
    uint256 deposited_after_1 = getNodeOperatorSigningStats_deposited(nodeOperatorId1);
    uint256 deposited_after_2 = getNodeOperatorSigningStats_deposited(nodeOperatorId2);

    assert (deposited_before_1 != deposited_after_1 && deposited_before_2 != deposited_after_2) 
        => nodeOperatorId1 == nodeOperatorId2;
}


// Checks that line 769 in NodeOperatorsRegistry.sol never overflows
rule targetPlusExitedDoesntOverflow(method f, uint256 nodeOperatorId)
filtered{f -> !f.isView} {
    env e1;
    env e2;
    calldataarg args;
    safeAssumptions_NOS(nodeOperatorId);

    // Assume doesn't overflow at first
    require getNodeOperatorSigningStats_exited(nodeOperatorId) +
    getNodeOperatorTargetStats_target(nodeOperatorId) <= UINT64_MAX();

    // Call any state-changing function
    f(e1, args);

    // Assume we're in the cleared penalty case:
    require isOperatorPenaltyCleared(e2, nodeOperatorId);

    // Assert the sum doesn't overflow again
    assert getNodeOperatorSigningStats_exited(nodeOperatorId) +
    getNodeOperatorTargetStats_target(nodeOperatorId) <= UINT64_MAX();
}
