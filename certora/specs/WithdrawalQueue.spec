import "./StEth.spec"

using StETHMock as STETH

methods {
    // WithdrawalQueue
    initialize(address, address, address, address, address) // check if one can initialize more than once and who can initialize.
    // isInitialized() returns (bool) envfree
    resume()
    pause(uint256)
    isPaused() returns (bool)
    claimWithdrawalTo(uint256, uint256, address)
    claimWithdrawal(uint256)
    finalize(uint256) //payable
    updateBunkerMode(bool, uint256)
    isBunkerModeActive() returns (bool) envfree
    bunkerModeSinceTimestamp() returns (uint256) envfree

    // WithdrawalQueueBase
    unfinalizedRequestNumber() returns (uint256) envfree
    unfinalizedStETH() returns (uint256) envfree
    findCheckpointHintUnbounded(uint256) returns (uint256) envfree
    findCheckpointHint(uint256, uint256, uint256) returns (uint256) envfree
    findLastFinalizableRequestIdByTimestamp(uint256, uint256, uint256) returns (uint256) envfree
    findLastFinalizableRequestIdByBudget(uint256, uint256, uint256, uint256) returns (uint256) envfree
    findLastFinalizableRequestId(uint256, uint256, uint256) returns (uint256) envfree
    finalizationBatch(uint256, uint256) returns (uint256, uint256) envfree

    // WithdrawalQueueHarness:
    getWithdrawalRequests(address)returns (uint256[]) envfree
    isRequestStatusClaimed(uint256) returns (bool) envfree
    isRequestStatusFinalized(uint256) returns (bool) envfree
    getRequestsStatusOwner(uint256) returns (address) envfree
    getRequestsStatusAmountOfShares(uint256) returns (uint256) envfree
    getRequestsStatusAmountOfStETH(uint256) returns (uint256) envfree
    requestWithdrawal(uint256, address) returns (uint256)
    claimWithdrawal(uint256, uint256)
    getFinalizedAndNotClaimedEth() returns (uint256) envfree

    // Getters:
    // WithdrawalQueueBase:
    getLastRequestId() returns (uint256) envfree
    getLastFinalizedRequestId() returns (uint256) envfree
    getLastCheckpointIndex() returns (uint256) envfree
    getLockedEtherAmount() returns (uint256) envfree

    // WithdrawalQueue:
    MIN_STETH_WITHDRAWAL_AMOUNT() returns (uint256) envfree
    MAX_STETH_WITHDRAWAL_AMOUNT() returns (uint256) envfree
    PAUSE_INFINITELY() returns (uint256) envfree
    BUNKER_MODE_DISABLED_TIMESTAMP() returns (uint256) envfree

    // WithdrawalQueueHarness:
    getRequestCumulativeStEth(uint256) returns(uint256) envfree
    getRequestCumulativeShares(uint256) returns(uint256) envfree
    balanceOfEth(address) returns (uint256) envfree
    getDiscountFactorByIndex(uint256) returns (uint96) envfree
    getFromRequestIdByIndex(uint256) returns (uint160) envfree
}

/**************************************************
 *               CVL FUNCS & DEFS                 *
 **************************************************/

definition E27_PRECISION_BASE() returns uint256 = 1000000000000000000000000000;

function calculateDiscountFactor(uint256 stETHAmount, uint256 ethAmount) returns uint256 {
    uint256 discountFactor;
    discountFactor = ethAmount * E27_PRECISION_BASE() / stETHAmount;
    return discountFactor;
}

/**************************************************
 *                METHOD INTEGRITY                *
 **************************************************/

/**
After calling requestWithdrawal:
    1. the stEth.shares of the user should decrease 
    2. the contract’s stEth.shares should increase by the same amount and 
    3. generate the desired withdrawal request.
 **/
rule integrityOfRequestWithdrawal(address owner, uint256 amount) {
    env e;
    require e.msg.sender != currentContract;
    uint256 stEthBalanceBefore = STETH.sharesOf(e.msg.sender);
    uint256 contractStEthBalanceBefore = STETH.sharesOf(currentContract);

    uint256 lastCumulativeStEth = getRequestCumulativeStEth(getLastRequestId());

    uint256 actualShares = STETH.getSharesByPooledEth(amount);

    uint256 requestId = requestWithdrawal(e, amount, owner);

    uint256 stEthBalanceAfter = STETH.sharesOf(e.msg.sender);
    uint256 contractStEthBalanceAfter = STETH.sharesOf(currentContract);
    uint256 reqCumulativeStEth = getRequestCumulativeStEth(requestId);

    assert requestId == getLastRequestId();
    assert stEthBalanceBefore - actualShares == stEthBalanceAfter;
    assert contractStEthBalanceBefore + actualShares == contractStEthBalanceAfter;
    assert reqCumulativeStEth == lastCumulativeStEth + amount;
}

/** 
After calling claimWithdrawal, if the user’s ETH balance was increased then:
    1.The locked ETH amount should decreased
    2.The request’s claimed and finalized flags are on.
    3.The request-id is smaller than the last finalized request id
**/
rule integrityOfClaimWithdrawal(uint256 requestId) {
    env e;
    require requestId > 0;
    requireInvariant cantWithdrawLessThanMinWithdrawal(requestId);
    requireInvariant cumulativeEtherGreaterThamMinWithdrawal(requestId);
    bool isClaimedBefore = isRequestStatusClaimed(requestId);
    bool isFinalized = isRequestStatusFinalized(requestId);
    uint256 ethBalanceBefore = balanceOfEth(e.msg.sender);
    uint256 lockedEthBefore = getLockedEtherAmount();
    
    claimWithdrawal(e, requestId);

    uint256 ethBalanceAfter = balanceOfEth(e.msg.sender);
    uint256 lockedEthAfter = getLockedEtherAmount();
    bool isClaimedAfter = isRequestStatusClaimed(requestId);

    assert ethBalanceAfter > ethBalanceBefore && lockedEthBefore > lockedEthAfter && 
                                                 !isClaimedBefore && isClaimedAfter && isFinalized &&
                                                 (requestId <= getLastFinalizedRequestId());
    assert ethBalanceAfter - ethBalanceBefore == lockedEthBefore - lockedEthAfter;
}

/** 
After calling finalize, the locked ETH amount is increased and the last finalized request-id should update accordingly
**/
rule integrityOfFinalize(uint256 _lastIdToFinalize) {
    env e;
    uint256 lockedEtherAmountBefore = getLockedEtherAmount();
    uint256 lastFinalizedRequestIdBefore = getLastFinalizedRequestId();

    finalize(e, _lastIdToFinalize);

    uint256 lockedEtherAmountAfter = getLockedEtherAmount();
    uint256 finalizedRequestsCounterAfter = getLastFinalizedRequestId();

    assert lockedEtherAmountAfter >= lockedEtherAmountBefore + e.msg.value;
    assert finalizedRequestsCounterAfter == _lastIdToFinalize;
    assert lastFinalizedRequestIdBefore <= _lastIdToFinalize;
}


/**************************************************
 *                   HIGH LEVEL                   *
 **************************************************/

/**
Check how finalizing with defferent requests are affecting the finalization
**/
rule finalizeAloneVsFinalizeBatch(uint256 requestId1, uint256 requestId2, uint256 shareRate) {
    env eClaimWithdrawal;
    env e1;
    env e2;
    requireInvariant cumulativeEthMonotonocInc(requestId1);
    requireInvariant cumulativeEthMonotonocInc(requestId2);
    // e.msg.value == max_uint256;
    storage init = lastStorage;
    address owner = getRequestsStatusOwner(requestId1);

    require owner != e1.msg.sender;

    require requestId1 + 1 == requestId2;
    require requestId2 < getLastRequestId();
    require requestId1 > getLastFinalizedRequestId();

    uint256 lockedEtherBefore = getLockedEtherAmount();

    uint256 ethToLock;
    uint256 sharesToBurn;
    ethToLock, sharesToBurn = finalizationBatch(requestId1, shareRate);
    require e1.msg.value == ethToLock;
    finalize(e1, requestId1);
    claimWithdrawal(eClaimWithdrawal, requestId1);

    uint256 userEthBalanceSeperate = balanceOfEth(owner);

    uint256 ethToLock2;
    uint256 sharesToBurn2;

    ethToLock2, sharesToBurn2 = finalizationBatch(requestId2, shareRate) at init;
    require e2.msg.value == ethToLock2; 

    finalize(e2, requestId2);
    claimWithdrawal(eClaimWithdrawal, requestId1);

    uint256 userEthBalanceBatch = balanceOfEth(owner);

    assert userEthBalanceSeperate == userEthBalanceBatch;
}

/** 
If there is a new checkpoint index then the last finalized request id must have grown,
**/
rule priceIndexFinalizedRequestsCounterCorelation(method f) {
    env e;
    calldataarg args;
    uint256 latestIndexBefore = getLastCheckpointIndex();
    uint256 finalizedRequestsCounterBefore = getLastFinalizedRequestId();

    f(e, args);

    uint256 latestIndexAfter = getLastCheckpointIndex();
    uint256 finalizedRequestsCounterAfter = getLastFinalizedRequestId();

    assert latestIndexAfter != latestIndexBefore => finalizedRequestsCounterAfter > finalizedRequestsCounterBefore;
}

/**
If there is a new checkpoint index then the discount factor must have changed
**/
rule newDiscountFactor(uint256 requestIdToFinalize) {
    env e;
    calldataarg args;

    requireInvariant cantWithdrawLessThanMinWithdrawal(requestIdToFinalize);

    uint256 amountOfEth = e.msg.value;
    uint256 lastFinilizedReqId = getLastFinalizedRequestId();
    uint256 amountOfStEth = getRequestCumulativeStEth(requestIdToFinalize) - getRequestCumulativeStEth(getLastFinalizedRequestId());

    require amountOfStEth > 0; // avoid dev by zero

    uint256 actualDiscountFactor = calculateDiscountFactor(amountOfStEth, amountOfEth);

    uint256 lastDiscountFactorBefore = getDiscountFactorByIndex(getLastCheckpointIndex());
    uint256 checkpointIndexLenBefore = getLastCheckpointIndex();

    require checkpointIndexLenBefore < max_uint256 - 1;

    finalize(e, requestIdToFinalize);

    uint256 lastDiscountFactorAfter = getDiscountFactorByIndex(getLastCheckpointIndex());
    uint256 checkpointIndexLenAfter = getLastCheckpointIndex();

    assert checkpointIndexLenAfter == checkpointIndexLenBefore + 1 <=> lastDiscountFactorAfter != lastDiscountFactorBefore;
    assert lastDiscountFactorAfter != lastDiscountFactorBefore => lastDiscountFactorAfter == actualDiscountFactor;
}

/**
Discount history is preserved
**/
rule preserveDiscountHistory(method f, uint256 index) 
    filtered{ f -> f.selector != initialize(address, address, address, address, address).selector } 
    {
    env e;
    calldataarg args;

    uint96 discountFactorBefore = getDiscountFactorByIndex(index);
    uint160 fromRequestIdBefore = getFromRequestIdByIndex(index);

    uint256 lastCheckPointIndexBefore = getLastCheckpointIndex();

    f(e, args);

    uint256 discountFactorAfter = getDiscountFactorByIndex(index);
    uint160 fromRequestIdAfter = getFromRequestIdByIndex(index);

    assert index <= lastCheckPointIndexBefore => (discountFactorBefore == discountFactorAfter && fromRequestIdBefore == fromRequestIdAfter);
}

/**
Claim the same withdrawal request twice and assert there are no changes after the second claim or the code reverts
**/
rule claimSameWithdrawalRequestTwice(uint256 requestId) {
    env e;
   
    claimWithdrawal(e, requestId);

    uint256 ethBalanceAfterFirst = balanceOfEth(e.msg.sender);
    uint256 lockedEthAfterFirst = getLockedEtherAmount();
    bool isClaimedAfterFirst = isRequestStatusClaimed(requestId);

    claimWithdrawal@withrevert(e, requestId);

    uint256 ethBalanceAfterSecond = balanceOfEth(e.msg.sender);
    uint256 lockedEthAfterSecond = getLockedEtherAmount();
    bool isClaimedAfterSecond = isRequestStatusClaimed(requestId);

    assert lastReverted || ethBalanceAfterFirst == ethBalanceAfterSecond;
    assert lastReverted || lockedEthAfterFirst == lockedEthAfterSecond;
    assert lastReverted || isClaimedAfterFirst && isClaimedAfterSecond;
}

/**
Claimed withdrawal request cant be unclaimed
**/
rule onceClaimedAlwaysClaimed(method f, uint256 requestId) {
    env e;
    calldataarg args;

    bool isClaimedBefore = isRequestStatusClaimed(requestId);

    f(e, args);

    bool isClaimedAfter = isRequestStatusClaimed(requestId);

    assert isClaimedBefore => isClaimedAfter;
}

/**************************************************
 *                   INVARIANTS                   *
 **************************************************/

/**
The last finalized request-id is always less than the last request-id
**/
invariant finalizedRequestsCounterisValid()
    getLastFinalizedRequestId() <= getLastRequestId()
/**
Cant withdraw less than the minimum amount or more than the maximum amount.
minimum withdrawal rule. min withdrawal == 0.1 ether == 10 ^ 17
**/
invariant cantWithdrawLessThanMinWithdrawal(uint256 reqId) 
    (reqId <= getLastRequestId() && reqId >= 1) => (
                                getRequestCumulativeStEth(reqId) - getRequestCumulativeStEth(reqId - 1) >= MIN_STETH_WITHDRAWAL_AMOUNT() &&
                                getRequestCumulativeStEth(reqId) - getRequestCumulativeStEth(reqId - 1) <= MAX_STETH_WITHDRAWAL_AMOUNT()
                            )
        {
            preserved 
            {
                requireInvariant cumulativeEtherGreaterThamMinWithdrawal(reqId);
                require reqId > 1;
            }
        }
                            

/**
Each request’s cumulative ETH must be greater than the minimum withdrawal amount
**/
invariant cumulativeEtherGreaterThamMinWithdrawal(uint256 reqId)
    (reqId <= getLastRequestId() && reqId >= 1) => (getRequestCumulativeStEth(reqId) >= MIN_STETH_WITHDRAWAL_AMOUNT())

/**
Cumulative ETH and cumulative shares are monotonic increasing
**/
invariant cumulativeEthMonotonocInc(uint256 reqId)
        reqId <= getLastRequestId() => (reqId > 0 => getRequestCumulativeStEth(reqId) > getRequestCumulativeStEth(reqId - 1)) &&
                                      (reqId > 0 => getRequestCumulativeShares(reqId) >= getRequestCumulativeShares(reqId - 1))
        {
            preserved 
            {
                require getRequestCumulativeStEth(0) == 0;
                require getRequestCumulativeShares(0) == 0;
            }
        }

/**
If the request-id is greater than the last finalized request-id then the request’s claimed and finalized flags are off
**/
invariant finalizedCounterFinalizedFlagCorrelation(uint256 requestId)
    requestId > getLastFinalizedRequestId() <=> !isRequestStatusFinalized(requestId)

/**
If a request is not claimed then it is not finalized
**/
invariant claimedFinalizedFlagsCorrelation(uint256 requestId)
    isRequestStatusClaimed(requestId) => isRequestStatusFinalized(requestId)

/**
Locked ETH should always be greater or equal to finalized and not claimed ether amount 
**/
invariant lockedEtherSolvency() 
    getLockedEtherAmount() >= getFinalizedAndNotClaimedEth()
        {
            preserved 
            {
                requireInvariant cantWithdrawLessThanMinWithdrawal(getLastFinalizedRequestId());
                require getRequestCumulativeStEth(0) == 0;
                require getRequestCumulativeShares(0) == 0;
            }
        }

rule lockedEtherSolvencyParametric(method f) {
    env e;
    calldataarg args;

    requireInvariant cantWithdrawLessThanMinWithdrawal(getLastFinalizedRequestId());
    require getRequestCumulativeStEth(0) == 0;
    require getRequestCumulativeShares(0) == 0;

    uint256 lockedAmountBefore = getLockedEtherAmount();
    uint256 FinalizedAndNotClaimedEthBefore = getFinalizedAndNotClaimedEth();

    require lockedAmountBefore >= FinalizedAndNotClaimedEthBefore;

    f(e, args);

    uint256 lockedAmountAfter = getLockedEtherAmount();
    uint256 FinalizedAndNotClaimedEthAfter = getFinalizedAndNotClaimedEth();

    assert lockedAmountAfter >= FinalizedAndNotClaimedEthAfter;
}


// RULES TO IMPLEMENT:

// rule for share rate: get min and max share rate within finalized batch, claim -> compute effective share rate and assert it is within range.
// hint monotonic increasing
// claim withdrawal with the wrong hint
// lockedEth >= finalized and not claimed
// finalize dont change fifo order of requests
// unique request ids.

// try to finalize more then ethBudget - budget comes from external call
// rule finalizeMoreThanETHBudget(uint256 requestIdToFinalize){
//     assert false;
// }
rule whoCanChangeUnfinalizedRequestsNumber(method f) {
    env e;
    calldataarg args;

    uint256 unfinalizedRequestNumberBefore = unfinalizedRequestNumber();

    f(e, args);

    uint256 unfinalizedRequestNumberAfter = unfinalizedRequestNumber();

    assert unfinalizedRequestNumberBefore == unfinalizedRequestNumberAfter;
}
