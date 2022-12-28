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

// rule integrityOfClaim() {

// }

rule integrityOfEnqueue(address recipient, uint256 etherAmount, uint256 sharesAmount) {
    env e;

    uint256 requestId = enqueue(e, recipient, etherAmount, sharesAmount);

    uint128 actualEtherAmount = getRequestsCumulativeEther(requestId);
    uint128 actualSharesAmount = getRequestsCumulativeShares(requestId);
    address actualRecipient = getRequestsRecipient(requestId);
    bool isClaimed = isRequestClaimed(requestId);
    
    assert actualEtherAmount == etherAmount;
    assert actualSharesAmount == sharesAmount;
    assert actualRecipient == recipient;
    assert !isClaimed;
}

// _sendValue function got native call - check for reentrency attack
 
