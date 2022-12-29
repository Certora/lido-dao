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
}

// sum all etherLocked is less or equal to lockedEath - not correct, EACH ONE AHOULD BE LESS OR EQUAL

// invariant - for all reqId1, reqId2 | if reqId1 > reqId2 => reqId1.cumulativeEther >= reqId2.cumulativeEther && reqId1.cumulativeShares >= reqId2.cumulativeShares.

rule integrityOfClaim(uint256 requestId, uint256 priceIndexHint) {
    env e;

    uint256 finalizedRequestsCount = finalizedRequestsCounter();
    bool isClaimedBefore = isRequestClaimed(_requestId);

    address recipient = claim(requestId, priceIndexHint);

    bool isClaimedAfter = isRequestClaimed(_requestId);

    assert requestId < finalizedRequestsCount;
    assert isClaimedAfter && !isClaimedBefore;
}

rule integrityOfEnqueue(address recipient, uint256 etherAmount, uint256 sharesAmount) {
    env e;
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

// // cumulativeEther is monotonicly increasing
// rule cumulativeEtherMonotonic(uint256 requestId) {
//     env e;
//     calldataarg args;

//     uint256 lastRequestId = queueLength() - 1;

//     uint256 requestId = enqueue(e, args);
// }

// rule sanity(method f) {
// 	env e;
// 	calldataarg arg;
// 	sinvoke f(e, arg);
// 	assert false;
// }

// _sendValue function got native call - check for reentrency attack
 
