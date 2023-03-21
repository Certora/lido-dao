methods{
    getRatio() returns(uint256) envfree
    getCLbalance() returns(uint256) envfree
    smoothenTokenRebase(uint256, uint256, uint256, uint256, uint256, uint256, uint256) returns(uint256,uint256,uint256) => DISPATCHER(true)
    getSharesRequestedToBurn() => DISPATCHER(true)
    checkAccountingOracleReport(uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)
}

// rule sanity(method f)
// {
//     env e;
//     calldataarg args;
//     f(e, args);
//     assert false;
// }

rule ratioNotGoDownWhenNoSlash()
{
    env e;
    calldataarg args;
    uint256 old_ratio = getRatio();
    uint256 old_cl_balance = getCLbalance();
    handleOracleReport(e, args);
    uint256 new_cl_balance = getCLbalance();
    require new_cl_balance == old_cl_balance;
    uint256 new_ratio = getRatio();
    assert new_ratio >= old_ratio;
}


// solvency
// check 
// 