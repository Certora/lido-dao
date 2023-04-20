methods{
    initialize(address, address)
    finalizeUpgrade_v2(address, address)
    pauseStaking()
    resumeStaking()
    setStakingLimit(uint256, uint256)
    removeStakingLimit()
    isStakingPaused() returns (bool) envfree
    getCurrentStakeLimit() returns (uint256) // envfree 
    getStakeLimitFullInfo() returns (bool, bool, uint256, uint256, uint256, uint256, uint256) // envfree
    submit(address) returns (uint256) //payable
    receiveELRewards() //payable
    receiveWithdrawals() //payable
    deposit(uint256, uint256, bytes)
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
    canDeposit() returns (bool) envfree
    getDepositableEther() returns (uint256) envfree

// StEth:
    getTotalPooledEther() returns (uint256) envfree  
    getTotalShares() returns (uint256) envfree     
    sharesOf(address) returns (uint256) envfree
    getSharesByPooledEth(uint256) returns (uint256) envfree
    getPooledEthByShares(uint256) returns (uint256) envfree
    transferShares(address, uint256) returns (uint256)
    transferSharesFrom(address, address, uint256) returns (uint256)

    getRatio() returns(uint256) envfree
    getCLbalance() returns(uint256) envfree
    smoothenTokenRebase(uint256, uint256, uint256, uint256, uint256, uint256, uint256) returns(uint256,uint256,uint256) => DISPATCHER(true)
    getSharesRequestedToBurn() => DISPATCHER(true)
    checkAccountingOracleReport(uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)

    // Harness:
    getStakingModuleMaxDepositsCount_workaround(uint256, uint256) returns (uint256) envfree

    // Summarizations:

    // WithdrawalQueue:
    isBunkerModeActive() => CONSTANT

    // LidoLocator:
    depositSecurityModule() => CONSTANT
    stakingRouter() => CONSTANT

    // StakingRouter:
    getStakingModuleMaxDepositsCount(uint256, uint256) => CONSTANT
}

rule integrityOfSubmit(address _referral) {
    env e;
    uint256 ethToSubmit = e.msg.value;
    uint256 old_stakeLimit = getCurrentStakeLimit(e);
    uint256 expectedShares = getSharesByPooledEth(ethToSubmit);
    
    uint256 shareAmount = submit(e, _referral);

    uint256 new_stakeLimit = getCurrentStakeLimit(e);

    assert (old_stakeLimit < max_uint256) => (new_stakeLimit == old_stakeLimit - ethToSubmit);
    assert expectedShares == shareAmount;
}

rule integrityOfDeposit(uint256 _maxDepositsCount, uint256 _stakingModuleId, bytes _depositCalldata) {
    env e;

    bool canDeposit = canDeposit();

    uint256 bufferedEthBefore = getBufferedEther();

    uint256 maxDepositsCountSR = getStakingModuleMaxDepositsCount_workaround(_stakingModuleId, getDepositableEther());

    deposit(e, _maxDepositsCount, _stakingModuleId, _depositCalldata);

    uint256 bufferedEthAfter = getBufferedEther();

    assert canDeposit;
    assert (_maxDepositsCount > 0 && maxDepositsCountSR > 0) => bufferedEthBefore > bufferedEthAfter;
}

// bunker state or protocol's pause state => can deposit

// balanceOf currentContract >= bufferedEth

// check what happends to get buffered eth if elRewardsToWithdraw is greater than the elRewardsVault's balance

