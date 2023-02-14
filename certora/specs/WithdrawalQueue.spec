methods {
    // WithdrawalQueue
    initialize(address, address, address, address, address) // check if one can initialize more than once and who can initialize.
    isInitialized() returns (bool) envfree
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
    finalizationBatch(uint256, uint256) returns (uint256, uint256)



    getWithdrawalRequests(address)returns (uint256[]) envfree
    isRequestStatusClaimed(uint256) returns (bool) envfree
    isRequestStatusFinalized(uint256) returns (bool) envfree
    getRequestsStatusOwner(uint256) returns (address) envfree
    getRequestsStatusAmountOfShares(uint256) returns (uint256) envfree
    getRequestsStatusAmountOfStETH(uint256) returns (uint256) envfree

    // Getters:
    // WithdrawalQueueBase:
    getLastRequestId() returns (uint256) envfree
    getLastFinalizedRequestId() returns (uint256) envfree
    getLastCheckpointIndex() returns (uint256) envfree
    getLockedEtherAmount() returns (uint256) envfree

    // WithdrawalQueue
    MIN_STETH_WITHDRAWAL_AMOUNT() returns (uint256) envfree
    MAX_STETH_WITHDRAWAL_AMOUNT() returns (uint256) envfree
    PAUSE_INFINITELY() returns (uint256) envfree
    BUNKER_MODE_DISABLED_TIMESTAMP() returns (uint256) envfree

    // WithdrawalQueueHarness
    balanceOfEth(address) returns (uint256) envfree
}

// rule sanity(method f)
// {
// 	env e;
// 	calldataarg arg;
// 	sinvoke f(e, arg);
// 	assert false;
// }

// // hint monotonic increasing

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

    assert ethBalanceAfter > ethBalanceBefore => requestId <= getLastFinalizedRequestId();
    assert ethBalanceAfter > ethBalanceBefore => lockedEthBefore > lockedEthAfter && !isClaimedBefore && isClaimedAfter && isFinalized;
    // assert ethBalanceAfter > ethBalanceBefore => ethBalanceAfter - ethBalanceBefore == lockedEthBefore - lockedEthAfter == amountOfEthStatus //TODO
}

// /**************************************************
//  *                METHOD INTEGRITY                *
//  **************************************************/

// rule integrityOfClaim(uint256 requestId, uint256 priceIndexHint) {
//     env e;

//     uint256 finalizedRequestsCount = finalizedRequestsCounter();
//     bool isClaimedBefore = isRequestClaimed(requestId);

//     address recipient = claim(requestId, priceIndexHint);

//     bool isClaimedAfter = isRequestClaimed(requestId);

//     assert requestId < finalizedRequestsCount;
//     assert isClaimedAfter && !isClaimedBefore;
// }

// rule integrityOfEnqueue(address recipient, uint256 etherAmount, uint256 sharesAmount) {
//     env e;
//     require queueLength() < max_uint256 - 1;
//     uint256 lastRequestId;
//     if (queueLength() > 0){
//         lastRequestId = queueLength() - 1;
//     } else {
//         lastRequestId = 0;
//     }
//     uint128 EtherAmountBefore = getRequestsCumulativeEther(lastRequestId);
//     uint128 SharesAmountBefore = getRequestsCumulativeShares(lastRequestId);

//     uint256 requestId = enqueue(e, recipient, etherAmount, sharesAmount);

//     uint128 actualEtherAmount = getRequestsCumulativeEther(requestId);
//     uint128 actualSharesAmount = getRequestsCumulativeShares(requestId);
//     address actualRecipient = getRequestsRecipient(requestId);
//     bool isClaimed = isRequestClaimed(requestId);
    
//     assert actualEtherAmount == etherAmount + EtherAmountBefore;
//     assert actualSharesAmount == sharesAmount + SharesAmountBefore;
//     assert actualRecipient == recipient;
//     assert !isClaimed;
// }

// rule integrityOfFinalize(uint256 _lastIdToFinalize, uint256 _etherToLock, uint256 _totalPooledEther, uint256 _totalShares) {
//     env e;
//     uint128 lockedEtherAmountBefore = lockedEtherAmount();

//     finalize(e, _lastIdToFinalize, _etherToLock, _totalPooledEther, _totalShares);

//     uint128 lockedEtherAmountAfter = lockedEtherAmount();
//     uint256 finalizedRequestsCounterAfter = finalizedRequestsCounter();

//     assert lockedEtherAmountAfter == lockedEtherAmountBefore + _etherToLock;
//     assert finalizedRequestsCounterAfter == _lastIdToFinalize + 1;
// }

// /**************************************************
//  *                   INVARIANTS                   *
//  **************************************************/

// invariant finalizedRequestsCounterLessThanEqToQueueLen()
//     finalizedRequestsCounter() <= queueLength()
//     {
//         preserved
//         {
//             require queueLength() < max_uint256 - 1;
//         }
//     }

// // minimum withdrawal rule. min withdrawal == 0.1 ether == 10 ^ 17
// invariant cantWithdrawLessThanMinWithdrawal(uint256 reqId) 
//     reqId < queueLength() => ((reqId > 0 => getRequestsCumulativeEther(reqId) - getRequestsCumulativeEther(reqId - 1) >= to_uint256(MIN_WITHDRAWAL())) 
//                           && (reqId == 0 => getRequestsCumulativeEther(reqId) >= to_uint256(MIN_WITHDRAWAL())))
//         {
//             preserved 
//             {
//                 requireInvariant finalizedRequestsCounterLessThanEqToQueueLen();
//                 require queueLength() < max_uint128;
//             }
//         }

// invariant solvency()
//     lockedEtherAmount() <= balanceOfEth(currentContract)

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

// function requirements(uint256 requestId, uint256 priceIndexHint) {
//     require !isPriceHintValid(requestId, priceIndexHint);
//     require requestId > finalizedRequestsCounter();
//     require queueLength() < max_uint128;
//     require getPricesLength() < max_uint128;
//     requireInvariant finalizedRequestsCounterLessThanEqToQueueLen();
// }

// // 1. request is queued, not finalized.
// // 2. finalize request
// // 3. user should get min(eth, shares * totalEth/ totalShares) (same params as finalize) - calculateFinalizationParamsForReqId vs finalize calculation
// // 4. claim request
// // 5. assert expected value == actual value.
// rule priceUpdateIntegrity(uint256 requestId, uint256 priceIndexHint, uint256 _lastIdToFinalize, uint256 _etherToLock, uint256 _totalPooledEther, uint256 _totalShares) {
//     env e;
//     uint256 priceLenBefore = getPricesLength();
//     requirements(requestId, priceIndexHint);
//     address recipient;
//     require recipient != 0 && recipient != currentContract;

//     uint256 recipientExpectedEth;
//     uint256 sharesToBurn;
//     recipientExpectedEth, sharesToBurn = calculateFinalizationParamsForReqId(requestId, _totalPooledEther, _totalShares);

//     finalize(e, _lastIdToFinalize, _etherToLock, _totalPooledEther, _totalShares); 

//     uint256 balanceOfBefore = balanceOfEth(recipient);
//     require isPriceHintValid(requestId, priceIndexHint);

//     require recipient == claim(requestId, priceIndexHint);

//     uint256 balanceOfAfter = balanceOfEth(recipient);
//     require priceLenBefore == getPricesLength();
//     assert balanceOfAfter - balanceOfBefore == recipientExpectedEth;
// }

// // RULES TO IMPLEMENT:

// // integrityOfRestake
// // invariant - for all reqId1, reqId2 | if reqId1 > reqId2 => reqId1.cumulativeEther >= reqId2.cumulativeEther && reqId1.cumulativeShares >= reqId2.cumulativeShares. *
// // if requestID > finalizedRequestsCounter => isClaimed == false
// // claim the same reqId twice
// // each etherLocked is less or equal to lockedEath
// // invariant - for all reqId1, reqId2 | if reqId1 > reqId2 => reqId1.cumulativeEther >= reqId2.cumulativeEther && reqId1.cumulativeShares >= reqId2.cumulativeShares.
