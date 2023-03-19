methods {
    STETH.name()                                returns (string) envfree
    STETH.symbol()                              returns (string) envfree
    STETH.decimals()                            returns (uint8) envfree   
    STETH.totalSupply()                         returns (uint256) envfree 
    STETH.balanceOf(address)                    returns (uint256) envfree 
    STETH.allowance(address,address)            returns (uint256) 
    STETH.approve(address,uint256)              returns (bool) 
    STETH.transfer(address,uint256)             returns (bool) 
    STETH.transferFrom(address,address,uint256) returns (bool) 
    STETH.increaseAllowance(address, uint256) returns (bool)  
    STETH.decreaseAllowance(address, uint256) returns (bool)  

    STETH.getTotalPooledEther() returns (uint256) envfree  
    STETH.getTotalShares() returns (uint256) envfree     
    STETH.sharesOf(address) returns (uint256) envfree
    STETH.getSharesByPooledEth(uint256) returns (uint256) envfree
    STETH.getPooledEthByShares(uint256) returns (uint256) envfree
    STETH.transferShares(address, uint256) returns (uint256)
    STETH.transferSharesFrom(address, address, uint256) returns (uint256) 
}

// // erc20 methods
// methods {
//     name()                                returns (string)  => DISPATCHER(true)
//     symbol()                              returns (string)  => DISPATCHER(true)
//     decimals()                            returns (uint8)   => DISPATCHER(true)
//     totalSupply()                         returns (uint256) envfree => DISPATCHER(true)
//     STETH.balanceOf(address)                    returns (uint256) envfree 
//     allowance(address,address)            returns (uint256) => DISPATCHER(true)
//     approve(address,uint256)              returns (bool)    => DISPATCHER(true)
//     transfer(address,uint256)             returns (bool)    => DISPATCHER(true)
//     transferFrom(address,address,uint256) returns (bool)    => DISPATCHER(true)
//     increaseAllowance(address, uint256) returns (bool)      => DISPATCHER(true)
//     decreaseAllowance(address, uint256) returns (bool)      => DISPATCHER(true)

//     getTotalPooledEther() returns (uint256) envfree         => DISPATCHER(true)
//     getTotalShares() returns (uint256) envfree              => DISPATCHER(true)
//     sharesOf(address) returns (uint256) envfree             => DISPATCHER(true)
//     getSharesByPooledEth(uint256) returns (uint256) envfree => DISPATCHER(true)
//     getPooledEthByShares(uint256) returns (uint256) envfree => DISPATCHER(true)
//     transferShares(address, uint256) returns (uint256)      => DISPATCHER(true)
//     transferSharesFrom(address, address, uint256) returns (uint256) => DISPATCHER(true)
// }

// rule sanity(method f)
// {
// 	env e;
// 	calldataarg arg;
// 	sinvoke f(e, arg);
// 	assert false;
// }
