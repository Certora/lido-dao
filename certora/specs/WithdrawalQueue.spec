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
}
