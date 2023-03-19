methods {
        supportsInterface(bytes4) returns (bool) envfree
        name() returns (string) envfree
        tokenURI(uint256) returns (string) envfree
        getNFTDescriptorAddress() returns (address) envfree
        setNFTDescriptorAddress(address)
        balanceOf(address) returns (uint256) envfree
        ownerOf(uint256) returns (address) envfree
        approve(address, uint256)
        getApproved(uint256) returns (address) envfree
        setApprovalForAll(address, bool)
        isApprovedForAll(address, address) returns (bool) envfree
}
