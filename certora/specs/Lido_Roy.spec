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
    // handle oracle report
    unsafeChangeDepositedValidators(uint256)
    handleOracleReport(uint256, uint256)
    transferToVault(address)
    getFee() returns (uint16) envfree
    getFeeDistribution() returns (uint16, uint16, uint16) envfree
    getWithdrawalCredentials() returns (bytes32) envfree
    getBufferedEther() returns (uint256) envfree
    getTotalELRewardsCollected() returns (uint256) envfree
    getOracle() returns (address) envfree
    getTreasury() returns (address) envfree
    getBeaconStat() returns (uint256, uint256, uint256) envfree
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
    LidoEthBalance() returns (uint256) envfree
    getEthBalance(address) returns (uint256) envfree
    // Summarizations:

    // WithdrawalQueue:
    isBunkerModeActive() => CONSTANT
    unfinalizedStETH() => UnfinalizedStETH()

    // LidoLocator:
    getLidoLocator() => ghostLidoLocator()
    depositSecurityModule() => ghostDSM()
    stakingRouter() => ghostStakingRouter()
    getRecoveryVault() => ghostRecoveryVault()
    treasury() => ghostTreasury()
    legacyOracle() => ghostLegacyOracle()
    withdrawalQueue() => ghostWithdrawalQueue()
    burner() => ghostBurner()
    withdrawalVault() => ghostWithdrawalVault()
    elRewardsVault() => ghostELRewardsVault()

    // StakingRouter:
    getStakingFeeAggregateDistributionE4Precision() => CONSTANT
    getStakingModuleMaxDepositsCount(uint256, uint256) => CONSTANT
    getWithdrawalCredentials() => ghostWithdrawalCredentials()
    getTotalFeeE4Precision() => ghostTotalFeeE4Precision()
    
    getApp(bytes32 a,bytes32 b) => getAppGhost(a, b)
    hashTypedDataV4(address _stETH, bytes32 _structHash) => ghostHashTypedDataV4(_stETH, _structHash)
    getScriptExecutor(bytes) => CONSTANT
    domainSeparatorV4(address) returns (bytes32) => CONSTANT
    eip712Domain(address) => DISPATCHER(true) // NONDET // Hopefully the nondeterministic behavior is not crucial
    canPerform(address, bytes32, uint256[]) => ALWAYS(true); // Warning: optimistic permission summary
    //hasPermission(address, address, bytes32, bytes) returns (bool) => ALWAYS(true);
    getEIP712StETH() => ghostEIP712StETH() //(assuming after initialize)
}

///
ghost ghostLidoLocator() returns address {
    axiom ghostLidoLocator() != currentContract;
    axiom ghostLidoLocator() != 0;
}

ghost ghostDSM() returns address {
    axiom ghostDSM() != currentContract;
    axiom ghostDSM() != 0;
} 

ghost ghostStakingRouter() returns address {
    axiom ghostStakingRouter() != currentContract;
    axiom ghostStakingRouter() != 0;
}

ghost ghostRecoveryVault() returns address {
    axiom ghostRecoveryVault() != currentContract;
    axiom ghostRecoveryVault() != 0;
}

ghost ghostTreasury() returns address {
    axiom ghostTreasury() != currentContract;
    axiom ghostTreasury() != 0;
}

ghost ghostBurner() returns address {
    axiom ghostBurner() != currentContract;
    axiom ghostBurner() != 0;
}

ghost ghostLegacyOracle() returns address {
    axiom ghostLegacyOracle() != currentContract;
    axiom ghostLegacyOracle() != 0;
}

ghost ghostWithdrawalQueue() returns address {
    axiom ghostWithdrawalQueue() != currentContract;
    axiom ghostWithdrawalQueue() != 0;
}

ghost ghostWithdrawalVault() returns address {
    axiom ghostWithdrawalVault() != currentContract;
    axiom ghostWithdrawalVault() != 0;
}

ghost ghostELRewardsVault() returns address {
    axiom ghostELRewardsVault() != currentContract;
    axiom ghostELRewardsVault() != 0;
}

ghost ghostEIP712StETH() returns address {
    axiom ghostEIP712StETH() != 0;
}

ghost ghostWithdrawalCredentials() returns bytes32;

ghost ghostTotalFeeE4Precision() returns uint16 {
    axiom to_mathint(ghostTotalFeeE4Precision()) <= 10000;
}

ghost getAppGhost(bytes32, bytes32) returns address {
    axiom forall bytes32 a . forall bytes32 b . 
        getAppGhost(a, b) != 0 && 
        getAppGhost(a, b) != currentContract;
}

ghost ghostHashTypedDataV4(address, bytes32) returns bytes32 {
    axiom forall address steth. forall bytes32 a .forall bytes32 b . 
        a != b => 
        ghostHashTypedDataV4(steth, a) != ghostHashTypedDataV4(steth, b);
}

ghost uint256 ghostUnfinalizedStETH;

function UnfinalizedStETH() returns uint256 {
    /// Needs to be havoc'd after some call (figure out when and how)
    return ghostUnfinalizedStETH;
}
///

function SumOfETHBalancesLEMAXUINT(address someUser) returns bool {
    mathint sum = 
        LidoEthBalance() + 
        getTotalELRewardsCollected() +
        getTotalPooledEther() +
        getEthBalance(ghostRecoveryVault()) +
        getEthBalance(ghostStakingRouter()) +
        getEthBalance(ghostWithdrawalQueue()) + 
        getEthBalance(ghostTreasury()) + 
        getEthBalance(ghostRecoveryVault()) + 
        getEthBalance(ghostDSM()) +
        getEthBalance(someUser);
    return sum <= max_uint;
}

definition isHandleReport(method f) returns bool = 
    f.selector == 
    handleOracleReport(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256[],uint256).selector;

definition isSubmit(method f) returns bool = 
    f.selector == submit(address).selector;

rule getSharesByPooledEthDoesntRevert(uint256 amount, method f) 
filtered{f -> !f.isView && !isHandleReport(f)} {
    env e;
    calldataarg args;
    getSharesByPooledEth(amount);
        f(e, args);
    getSharesByPooledEth@withrevert(amount);

    assert !lastReverted;
}

rule submitCannotDoSFunctions(method f) 
filtered{f -> !(isHandleReport(f) || isSubmit(f))} {
    env e1; 
    env e2;
    require e2.msg.sender != currentContract;
    calldataarg args;
    address referral;
    uint256 amount;

    storage initState = lastStorage;
    require SumOfETHBalancesLEMAXUINT(e2.msg.sender);
    
    f(e1, args);
    
    submit(e2, referral) at initState;
    // assuming getSharesPyPooledEth doesn't revert
    getSharesByPooledEth(amount);

    f@withrevert(e1, args);

    assert !lastReverted;
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
    uint256 stakeLimit = getCurrentStakeLimit(e);
    uint256 bufferedEthBefore = getBufferedEther();

    uint256 maxDepositsCountSR = getStakingModuleMaxDepositsCount_workaround(_stakingModuleId, getDepositableEther());

    deposit(e, _maxDepositsCount, _stakingModuleId, _depositCalldata);

    uint256 bufferedEthAfter = getBufferedEther();

    assert canDeposit;
    assert (_maxDepositsCount > 0 && maxDepositsCountSR > 0) => bufferedEthBefore > bufferedEthAfter;
    assert bufferedEthBefore - bufferedEthAfter <= bufferedEthBefore;
}

