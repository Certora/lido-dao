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

rule integrityOfClaimWithdrawal(uint256 requestId) {
    env e;
    bool isClaimedBefore = isRequestStatusClaimed(requestId);
    bool isFinalized = isRequestStatusFinalized(requestId);
    uint256 ethBalanceBefore = balanceOfEth(e.msg.sender);
    uint256 lockedEthBefore = getLockedEtherAmount();
    
    claimWithdrawal(e, requestId);

    uint256 ethBalanceAfter = balanceOfEth(e.msg.sender);
    uint256 lockedEthAfter = getLockedEtherAmount();
    bool isClaimedAfter = isRequestStatusClaimed(requestId);

    assert ethBalanceAfter > ethBalanceBefore => lockedEthBefore > lockedEthAfter && 
                                                 !isClaimedBefore && isClaimedAfter && isFinalized &&
                                                 (requestId <= getLastFinalizedRequestId());
    assert ethBalanceAfter - ethBalanceBefore == lockedEthBefore - lockedEthAfter;
}

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
    require requestId1 < getLastRequestId() && requestId2 < getLastRequestId();
    require requestId1 > getLastFinalizedRequestId() && requestId2 > getLastFinalizedRequestId();

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

rule newDiscountFactor(uint256 requestIdToFinalize) {
    env e;
    calldataarg args;

    requireInvariant cantWithdrawLessThanMinWithdrawal(requestIdToFinalize);

    uint256 amountOfEth = e.msg.value;
    uint256 lastFinilizedReqId = getLastFinalizedRequestId();
    uint256 amountOfStEth = getRequestCumulativeStEth(requestIdToFinalize) - getRequestCumulativeStEth(getLastFinalizedRequestId());

    require amountOfStEth > 0;

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

// try to finalize more then ethBudget
rule finalizeMoreThanETHBudget(uint256 requestIdToFinalize){
    assert false;
}

/**************************************************
 *                   INVARIANTS                   *
 **************************************************/

invariant finalizedRequestsCounterisValid()
    getLastFinalizedRequestId() <= getLastRequestId()

// minimum withdrawal rule. min withdrawal == 0.1 ether == 10 ^ 17
invariant cantWithdrawLessThanMinWithdrawal(uint256 reqId) 
    reqId <= getLastRequestId() => (
                               (
                                reqId >= 1 => (getRequestCumulativeStEth(reqId) - getRequestCumulativeStEth(reqId - 1) >= MIN_STETH_WITHDRAWAL_AMOUNT() &&
                                getRequestCumulativeStEth(reqId) - getRequestCumulativeStEth(reqId - 1) <= MAX_STETH_WITHDRAWAL_AMOUNT())
                               ) 
                            // && (
                            //     reqId == 1 => ((getRequestCumulativeStEth(reqId) >= MIN_STETH_WITHDRAWAL_AMOUNT()) && 
                            //     getRequestCumulativeStEth(reqId) <= MAX_STETH_WITHDRAWAL_AMOUNT())
                            //    )
                            )
        {
            preserved 
            {
                requireInvariant cumulativeEtherGreaterThamMinWithdrawal(reqId);
                require reqId > 1;
            }
        }
                            

invariant cumulativeEtherGreaterThamMinWithdrawal(uint256 reqId)
    reqId <= getLastRequestId() && reqId >= 1 => (getRequestCumulativeStEth(reqId) >= MIN_STETH_WITHDRAWAL_AMOUNT())

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

// RULES TO IMPLEMENT:

// rule for share rate: get min and max share rate within finalized batch, claim -> compute effective share rate and assert it is within range.
// hint monotonic increasing
// claim withdrawal with the wrong hint
// who can increase or decrease unfinilized requests number
// rule claimed cant be unclaimed

// whoCanClaimRequests

// claim with the wrong hint
rule whoCanChangeUnfinalizedRequestsNumber(method f) {
    env e;
    calldataarg args;

    uint256 unfinalizedRequestNumberBefore = unfinalizedRequestNumber();

    f(e, args);

    uint256 unfinalizedRequestNumberAfter = unfinalizedRequestNumber();

    assert false;
}

// rule finalizeSeperateVsFinalizeBatch(uint256 _lastIdToFinalize) {
//     // finanlize two requests seperatly and compare with finalize both together (with lastStorage) and compare 
// }

// rule finalizeAndClaimSeperateVsBatch(uint256 _lastIdToFinalize) {
//     // finanlize two requests seperatly and compare with finalize both together (with lastStorage) and compare 
// }

// /**************************************************
//  *                   INVARIANTS                   *
//  **************************************************/

// invariant lastHintIndexEqFinalizedRequestsCounter()
//     getPriceIndex(getFinalizationPricesLength() - 1) + 1 == finalizedRequestsCounter()
    
// // invariant to verify that priceIndex is monotonic increasing *
// invariant checkPriceIndex(uint256 hint) 
//     (hint < getFinalizationPricesLength() && hint >= 1) => getPriceIndex(hint) > getPriceIndex(hint - 1)
//     {
//         preserved {
//             requireInvariant lastHintIndexEqFinalizedRequestsCounter();
//             require getFinalizationPricesLength() < max_uint128;
//         }
//     }

// rule priceIndexFinalizedRequestsCounterCorelation(method f) {
//     env e;
//     calldataarg args;
//     uint256 latestIndexBefore;
//     if(getPricesLength() > 0){
//         latestIndexBefore = getPriceIndex(getPricesLength() - 1);
//     } else {
//         latestIndexBefore = 0;
//     }
//     uint256 finalizedRequestsCounterBefore = finalizedRequestsCounter();
//     uint256 pricesLenBefore = getPricesLength();

//     f(e, args);

//     uint256 latestIndexAfter = getPriceIndex(getPricesLength() - 1);
//     uint256 finalizedRequestsCounterAfter = finalizedRequestsCounter();
//     uint256 pricesLenAfter = getPricesLength();

//     assert pricesLenAfter > pricesLenBefore || latestIndexAfter != latestIndexBefore => finalizedRequestsCounterAfter > finalizedRequestsCounterBefore;
// }


// // irrelevant
// invariant solvency()
//     getLockedEtherAmount() <= balanceOfEth(currentContract)

// // RULES TO IMPLEMENT:

// // invariant - for all reqId1, reqId2 | if reqId1 > reqId2 => reqId1.cumulativeEther >= reqId2.cumulativeEther && reqId1.cumulativeShares >= reqId2.cumulativeShares. *
// // if requestID > finalizedRequestsCounter => isClaimed == false
// // claim the same reqId twice
// // each etherLocked is less or equal to lockedEath
