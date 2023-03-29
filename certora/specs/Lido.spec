methods{
    pauseStaking()
    resumeStaking()
    setStakingLimit(uint256, uint256)
    removeStakingLimit()
    isStakingPaused() returns (bool) envfree
    getCurrentStakeLimit() returns (uint256) envfree
    getStakeLimitFullInfo() returns (bool, bool, uint256, uint256, uint256, uint256, uint256) envfree
    submit(address) returns (uint256) //payable
    receiveELRewards() //payable
    depositBufferedEther()
    depositBufferedEther(uint256)
    burnShares(address, uint256) returns (uint256)
    stop()
    resume()
    setFee(uint16)
    setFeeDistribution(uint16, uint16, uint16)
    setProtocolContracts(address, address, address)
    setWithdrawalCredentials(bytes32)
    setELRewardsVault(address)
    setELRewardsWithdrawalLimit(uint16)
    handleOracleReport(uint256, uint256)
    transferToVault(address)
    getFee() returns (uint16) envfree
    getFeeDistribution() returns (uint16, uint16, uint16) envfree
    getWithdrawalCredentials() returns (bytes32) envfree
    getBufferedEther() returns (uint256) envfree
    getTotalELRewardsCollected() returns (uint256) envfree
    getELRewardsWithdrawalLimit() returns (uint256) envfree
    // getDepositContract() public view returns (IDepositContract)
    getOracle() returns (address) envfree
    // getOperators() public view returns (INodeOperatorsRegistry)
    getTreasury() returns (address) envfree
    getInsuranceFund() returns (address) envfree
    getBeaconStat() returns (uint256, uint256, uint256) envfree
    getELRewardsVault() returns (address) envfree


    getRatio() returns(uint256) envfree
    getCLbalance() returns(uint256) envfree
    smoothenTokenRebase(uint256, uint256, uint256, uint256, uint256, uint256, uint256) returns(uint256,uint256,uint256) => DISPATCHER(true)
    getSharesRequestedToBurn() => DISPATCHER(true)
    checkAccountingOracleReport(uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)
}



