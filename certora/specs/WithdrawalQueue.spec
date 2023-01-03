methods {
    queueLength() returns (uint256) envfree
    claim(uint256, uint256) returns (address) envfree
    calculateFinalizationParams(uint256, uint256, uint256) returns (uint256, uint256) envfree
    findPriceHint(uint256) returns (uint256) envfree

    //onlyOwner
    enqueue(address, uint256, uint256) returns (uint256)
    restake(uint256)

    //payable
    finalize(uint256, uint256, uint256, uint256)

    // Getters:
    finalizedRequestsCounter() returns (uint256) envfree
    lockedEtherAmount() returns (uint128) envfree
    getRequestsCumulativeEther(uint256) returns (uint128) envfree
    getRequestsCumulativeShares(uint256) returns (uint128) envfree
    getRequestsRecipient(uint256) returns (address) envfree
    isRequestClaimed(uint256) returns (bool) envfree
    balnceOfEth(address) returns(uint256) envfree
    getPricesLength() returns (uint256) envfree
    MIN_WITHDRAWAL() returns (uint256) envfree
    getFinalizationPricesLength() returns (uint256) envfree
    getPriceIndex(uint256) returns (uint256) envfree

    // Harness:
    calculateFinalizationParamsForReqId(uint256, uint256, uint256) returns (uint256, uint256) envfree
    isPriceHintValid(uint256, uint256) returns (bool isInRange) envfree
}

/**************************************************
 *                METHOD INTEGRITY                *
 **************************************************/

rule integrityOfClaim(uint256 requestId, uint256 priceIndexHint) {
    env e;

    uint256 finalizedRequestsCount = finalizedRequestsCounter();
    bool isClaimedBefore = isRequestClaimed(requestId);

    address recipient = claim(requestId, priceIndexHint);

    bool isClaimedAfter = isRequestClaimed(requestId);

    assert requestId < finalizedRequestsCount;
    assert isClaimedAfter && !isClaimedBefore;
}

rule integrityOfEnqueue(address recipient, uint256 etherAmount, uint256 sharesAmount) {
    env e;
    require queueLength() < max_uint256 - 1;
    uint256 lastRequestId = queueLength() - 1;
    uint128 EtherAmountBefore = getRequestsCumulativeEther(lastRequestId);
    uint128 SharesAmountBefore = getRequestsCumulativeShares(lastRequestId);

    uint256 requestId = enqueue(e, recipient, etherAmount, sharesAmount);

    uint128 actualEtherAmount = getRequestsCumulativeEther(requestId);
    uint128 actualSharesAmount = getRequestsCumulativeShares(requestId);
    address actualRecipient = getRequestsRecipient(requestId);
    bool isClaimed = isRequestClaimed(requestId);
    
    assert actualEtherAmount == etherAmount + EtherAmountBefore;
    assert actualSharesAmount == sharesAmount + SharesAmountBefore;
    assert actualRecipient == recipient;
    assert !isClaimed;
}

rule integrityOfFinialize(uint256 _lastIdToFinalize, uint256 _etherToLock, uint256 _totalPooledEther, uint256 _totalShares) {
    env e;
    uint128 lockedEtherAmountBefore = lockedEtherAmount();

    finalize(e, _lastIdToFinalize, _etherToLock, _totalPooledEther, _totalShares);

    uint128 lockedEtherAmountAfter = lockedEtherAmount();
    uint256 finalizedRequestsCounterAfter = finalizedRequestsCounter();

    assert lockedEtherAmountAfter == lockedEtherAmountBefore + _etherToLock;
    assert finalizedRequestsCounterAfter == _lastIdToFinalize + 1;
}

/**************************************************
 *                   INVARIANTS                   *
 **************************************************/

// minimum withdrawal rule. min withdrawal == 0.1 ether == 10 ^ 17
invariant cantWithdrawLessThanMinWithdrawal() 
    forall uint256 reqId . reqId < queueLength() && reqId >= 1 => getRequestsCumulativeEther(reqId) - getRequestsCumulativeEther(reqId - 1) >= to_uint256(MIN_WITHDRAWAL())
        {
            preserved 
            {
                requireInvariant finalizedRequestsCounterLessThanEqToQueueLen();
            }
        }

invariant lastHintIndexEqFinalizedRequestsCounter()
    getPriceIndex(getFinalizationPricesLength() - 1) + 1 == finalizedRequestsCounter()
    

invariant checkPriceIndex() 
    forall uint256 hint . (hint < getFinalizationPricesLength() && hint >= 1) => getPriceIndex(hint) > getPriceIndex(hint - 1)
    {
        preserved{
            requireInvariant lastHintIndexEqFinalizedRequestsCounter();
        }
    }

// each etherLocked is less or equal to lockedEath *
invariant lockedEathIsGraterThanCumulativeEther() 
    forall uint256 reqId . reqId < finalizedRequestsCounter() && !isRequestClaimed(reqId) && reqId >= 1 => getRequestsCumulativeEther(reqId) - getRequestsCumulativeEther(reqId - 1) <= lockedEtherAmount()
        {
            preserved 
            {
                requireInvariant finalizedRequestsCounterLessThanEqToQueueLen();
            }
        }

invariant contractHasEnoughEth()
    lockedEtherAmount() <= balnceOfEth(currentContract)

invariant finalizedRequestsCounterLessThanEqToQueueLen()
    finalizedRequestsCounter() <= queueLength()

// invariant - for all reqId1, reqId2 | if reqId1 > reqId2 => reqId1.cumulativeEther >= reqId2.cumulativeEther && reqId1.cumulativeShares >= reqId2.cumulativeShares. *


rule priceIndexFinalizedRequestsCounterCorelation(method f) {
    env e;
    calldataarg args;

    uint256 latestIndexBefore = getPriceIndex(getPricesLength() - 1);
    uint256 finalizedRequestsCounterBefore = finalizedRequestsCounter();
    uint256 pricesLenBefore = getPricesLength();


    f(e, args);

    uint256 latestIndexAfter = getPriceIndex(getPricesLength() - 1);
    uint256 finalizedRequestsCounterAfter = finalizedRequestsCounter();
    uint256 pricesLenAfter = getPricesLength();

    assert pricesLenAfter > pricesLenBefore || latestIndexAfter != latestIndexBefore => finalizedRequestsCounterAfter > finalizedRequestsCounterBefore;
}

// 1. request is queued, not finalized.
// 2. fanalize request
// 3. user should get min(eth, shares * totalEth/ totalShares) (same params as finalize)
// 4. claim request
// 5. assert expected value == actual value.

rule priceUpdateIntegrity(uint256 requestId, uint256 priceIndexHint, uint256 _lastIdToFinalize, uint256 _etherToLock, uint256 _totalPooledEther, uint256 _totalShares) {
    env e;
    uint256 priceLenBefore = getPricesLength();
    uint256 finalizedRequestsCount = finalizedRequestsCounter();
    bool isClaimed = isRequestClaimed(requestId);
    require !isPriceHintValid(requestId, priceIndexHint);
    require requestId > finalizedRequestsCount;
    require !isClaimed;

    address recipient;
    require recipient != 0 && recipient != currentContract;

    uint256 etherToLock;
    uint256 sharesToBurn;
    etherToLock, sharesToBurn = calculateFinalizationParamsForReqId(requestId, _totalPooledEther, _totalShares);
    finalize(e, _lastIdToFinalize, _etherToLock, _totalPooledEther, _totalShares); 
    uint256 balanceOfBefore = balnceOfEth(recipient);
    require isPriceHintValid(requestId, priceIndexHint);
    require recipient == claim(requestId, priceIndexHint);
    uint256 balanceOfAfter = balnceOfEth(recipient);
    require priceLenBefore == getPricesLength();
    assert balanceOfAfter - balanceOfBefore == etherToLock;
   
}

// RULES TO IMPLEMENT:

// integrityOfRestake

// invariant - for all reqId1, reqId2 | if reqId1 > reqId2 => reqId1.cumulativeEther >= reqId2.cumulativeEther && reqId1.cumulativeShares >= reqId2.cumulativeShares. *

// invariant for hintIndex -> monotonic increasing *
// rule hintIndexMonotonicIncreasing() {
    
// }

// finalizedRequestsCounter == lastHintIndex /+-1 - corelation if index inc then finalized inc

// if requestID > finalizedRequestsCounter => isClaimed == false

// invariant(uint256 reqId)
//     reqId > finalizedRequestsCount() => !isClaimed(reqId)

// claim the same reqId twice

 
/**************************************************
 *               CVL FUNCS & DEFS                 *
 **************************************************/

/**************************************************
 *               STATE TRANSITIONS                *
 **************************************************/

/**************************************************
 *                 VALID STATES                   *
 **************************************************/
