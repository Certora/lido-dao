methods{
    smoothenTokenRebase(uint256, uint256, uint256, uint256, uint256, uint256, uint256) returns(uint256,uint256,uint256) => DISPATCHER(true)
    checkAccountingOracleReport(uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)
    withdrawWithdrawals(uint256) => DISPATCHER(true)
    commitSharesToBurn(uint256) => DISPATCHER(true)
    getSharesRequestedToBurn() => DISPATCHER(true)
    withdrawRewards(uint256) => DISPATCHER(true)
    receiveWithdrawals() => DISPATCHER(true)
    receiveELRewards() => DISPATCHER(true)
    getMaxPositiveTokenRebase() => DISPATCHER(true)
    getPooledEthByShares(uint256) => DISPATCHER(true)
    requestBurnShares(address, uint256) => DISPATCHER(true)
    transferSharesFrom(address, address, uint256) => DISPATCHER(true)
    _approve(address, address, uint256) => DISPATCHER(true)
    _transferShares(address, address, uint256) => DISPATCHER(true)
    checkSimulatedShareRate(uint256,uint256,uint256,uint256,uint256) => DISPATCHER(true)
    getCLvalidators() returns(uint256) envfree
    getTotalAssetEth() returns(uint256) envfree
    getTotalShares() returns(uint256) envfree
    getCLbalance() returns(uint256) envfree
    getRatio() returns(uint256) envfree
    getMaxRebase(address) returns(uint256) envfree
    
    checkWithdrawalQueueOracleReport(uint256, uint256) => NONDET
    finalizationBatch(uint256 a, uint256 b) returns(uint256,uint256)=> NONDET
    oracleReportComponentsForLido()=> NONDET
    withdrawalVault() => NONDET
    elRewardsVault() => NONDET
    getLidoLocator() => NONDET
    finalize(uint256) => NONDET
    isPaused() => NONDET
    _distributeFee(uint256,uint256,uint256) => NONDET
    handlePostTokenRebase(uint256, uint256, uint256, uint256, uint256, uint256, uint256) => NONDET
}
definition ETHER() returns uint256 = 1000000 * 1000000 * 1000000; 
// function calcWithdraw() returns(uint256,uint256) {
//     return ETHER()*40000, ETHER()*40000;
// }

// rule sanity(method f)
// {
//     env e;
//     calldataarg args;
//     f(e, args);
//     assert false;
// }
//10**18


rule ratioNotGoDownWhenNoSlash()
{
    env e;
    calldataarg args;
    uint256 old_ratio = getRatio();
    uint256 oldAssets = getTotalAssetEth();
    uint256 oldShares = getTotalShares();
    require oldAssets == 1000000 * ETHER();
    require oldShares == 1000000 * ETHER();
    uint256 old_cl_balance = getCLbalance();
    uint256 old_validators = getCLvalidators();
    calldataarg args2;
    uint256 rebase = getMaxRebase(args2);
    require rebase == 1000000; // 0.1%
    handleOracleReport(e, args);
    uint256 newAssets = getTotalAssetEth();
    uint256 newShares = getTotalShares();
    require newAssets == 961000 * ETHER();
    require newShares >= 961000 * ETHER();
    // require newShares <= 961539 * ETHER();
    uint256 new_cl_balance = getCLbalance();
    require new_cl_balance == old_cl_balance;
    uint256 new_validators = getCLvalidators();
    require old_validators == new_validators;
    uint256 new_ratio = getRatio();
    assert new_ratio >= old_ratio;
}

// rule 


// rule bug()
// {
//     uint256 oldShares = getTotalShares();
//     t();
//     uint256 Shares = getTotalShares();
//     assert oldShares == Shares;
// }

// solvency
// check 
// 