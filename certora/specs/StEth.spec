methods {
    name()                                returns (string) envfree
    ymbol()                              returns (string) envfree
    decimals()                            returns (uint8) envfree   
    totalSupply()                         returns (uint256) envfree 
    balanceOf(address)                    returns (uint256) envfree 
    allowance(address,address)            returns (uint256) envfree
    approve(address,uint256)              returns (bool) 
    transfer(address,uint256)             returns (bool) 
    transferFrom(address,address,uint256) returns (bool) 
    increaseAllowance(address, uint256) returns (bool)  
    decreaseAllowance(address, uint256) returns (bool)  

    getTotalPooledEther() returns (uint256) envfree  
    getTotalShares() returns (uint256) envfree     
    sharesOf(address) returns (uint256) envfree
    getSharesByPooledEth(uint256) returns (uint256) envfree
    getPooledEthByShares(uint256) returns (uint256) envfree
    transferShares(address, uint256) returns (uint256)
    transferSharesFrom(address, address, uint256) returns (uint256)

    // Lido
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

    getIsStopped() returns (bool) envfree

    // mint(address,uint256)
    // burn(uint256)
    // burn(address,uint256)
    // burnFrom(address,uint256)
    // initialize(address)
}

// function doesntChangeBalance(method f) returns bool {
//     return f.selector != transfer(address,uint256).selector &&
//         f.selector != transferFrom(address,address,uint256).selector &&
//         f.selector != mint(address,uint256).selector &&
//         f.selector != burn(uint256).selector &&
//         f.selector != burn(address,uint256).selector &&
//         f.selector != burnFrom(address,uint256).selector &&
//         f.selector != initialize(address).selector;
// }

/*
    @Rule


    @Description:
        Verify that there is no fee on transferFrom() (like potentially on USDT)

    @Notes:


    @Link:

*/
rule noFeeOnTransferFrom(address alice, address bob, uint256 amount) {
    env e;
    require alice != bob;
    require allowance(alice, e.msg.sender) >= amount;
    uint256 sharesBalanceBeforeBob = sharesOf(bob);
    uint256 sharesBalanceBeforeAlice = sharesOf(alice);

    uint256 actualSharesAmount = getSharesByPooledEth(amount);

    transferFrom(e, alice, bob, amount);

    uint256 sharesBalanceAfterBob = sharesOf(bob);
    uint256 sharesBalanceAfterAlice = sharesOf(alice);

    assert sharesBalanceAfterBob <= sharesBalanceBeforeBob + actualSharesAmount;
    assert sharesBalanceAfterAlice <= sharesBalanceBeforeAlice - actualSharesAmount;
}

/*
    @Rule

    @Description:
        Verify that there is no fee on transfer() (like potentially on USDT)
    
    @Notes:
    
    @Link:


*/
rule noFeeOnTransfer(address bob, uint256 amount) {
    env e;
    require bob != e.msg.sender;
    uint256 balanceSenderBefore = sharesOf(e.msg.sender);
    uint256 balanceBefore = sharesOf(bob);

    uint256 actualSharesAmount = getSharesByPooledEth(amount);

    transfer(e, bob, amount);

    uint256 balanceAfter = sharesOf(bob);
    uint256 balanceSenderAfter = sharesOf(e.msg.sender);
    assert balanceAfter == balanceBefore + actualSharesAmount;
    assert balanceSenderAfter == balanceSenderBefore - actualSharesAmount;
}

/*
    @Rule


    @Description:
        Token transfer works correctly. Balances are updated if not reverted. 
        If reverted then the transfer amount was too high, or the recipient either 0, the same as the sender or the currentContract.


    @Notes:
        This rule fails on tokens with a blacklist function, like USDC and USDT.
        The prover finds a counterexample of a reverted transfer to a blacklisted address or a transfer in a paused state.

    @Link:

*/
rule transferCorrect(address to, uint256 amount) {
    env e;
    require e.msg.value == 0 && e.msg.sender != 0;
    uint256 fromBalanceBefore = sharesOf(e.msg.sender);
    uint256 toBalanceBefore = sharesOf(to);
    require fromBalanceBefore + toBalanceBefore <= max_uint256;
    require getIsStopped() == false;
    uint256 actualSharesAmount = getSharesByPooledEth(amount);

    transfer@withrevert(e, to, amount);
    bool reverted = lastReverted;
    if (!reverted) {
        if (e.msg.sender == to) {
            assert sharesOf(e.msg.sender) == fromBalanceBefore;
        } else {
            assert sharesOf(e.msg.sender) == fromBalanceBefore - actualSharesAmount;
            assert sharesOf(to) == toBalanceBefore + actualSharesAmount;
        }
    } else {
        assert actualSharesAmount > fromBalanceBefore || to == 0 || e.msg.sender == to || to == currentContract;
    }
}

/*
    @Rule


    @Description:
        Test that transferFrom works correctly. Balances are updated if not reverted. 
        If reverted, it means the transfer amount was too high, or the recipient is 0

    @Notes:
        This rule fails on tokens with a blacklist and or pause function, like USDC and USDT.
        The prover finds a counterexample of a reverted transfer to a blacklisted address or a transfer in a paused state.

    @Link:

*/

rule transferFromCorrect(address from, address to, uint256 amount) {
    env e;
    require e.msg.value == 0;
    uint256 fromBalanceBefore = sharesOf(from);
    uint256 toBalanceBefore = sharesOf(to);
    uint256 allowanceBefore = allowance(from, e.msg.sender);
    require fromBalanceBefore + toBalanceBefore <= max_uint256;
    uint256 actualSharesAmount = getSharesByPooledEth(amount);

    transferFrom(e, from, to, amount);

    assert from != to =>
        sharesOf(from) == fromBalanceBefore - actualSharesAmount &&
        sharesOf(to) == toBalanceBefore + actualSharesAmount &&
        allowance(from, e.msg.sender) == allowanceBefore - amount;
}

/*
    @Rule

    @Description:
        transferFrom should revert if and only if the amount is too high or the recipient is 0.

    @Notes:
        Fails on tokens with pause/blacklist functions, like USDC.

    @Link:

*/
rule transferFromReverts(address from, address to, uint256 amount) {
    env e;
    uint256 allowanceBefore = allowance(from, e.msg.sender);
    uint256 fromBalanceBefore = sharesOf(from);
    require from != 0 && e.msg.sender != 0;
    require e.msg.value == 0;
    require fromBalanceBefore + sharesOf(to) <= max_uint256;
    require getIsStopped() == false;
    uint256 actualSharesAmount = getSharesByPooledEth(amount);

    transferFrom@withrevert(e, from, to, amount);

    assert lastReverted <=> (allowanceBefore < amount || actualSharesAmount > fromBalanceBefore || to == 0 || to == currentContract);
}

// /*
//     @Rule

//     @Description:
//         Balance of address 0 is always 0

//     @Notes:


//     @Link:

// */
// invariant ZeroAddressNoBalance()
//     balanceOf(0) == 0

/*
    @Rule

    @Description:
        Allowance changes correctly as a result of calls to approve, transferFrom, transferSharesFrom, increaseAllowance, decreaseAllowance


    @Notes:
        Some ERC20 tokens have functions like permit() that change allowance via a signature. 
        The rule will fail on such functions.

    @Link:

*/
rule ChangingAllowance(method f, address from, address spender) 
    filtered{ f -> f.selector != initialize(address, address).selector || f.selector != finalizeUpgrade_v2(address,address).selector } {
    uint256 allowanceBefore = allowance(from, spender);
    env e;
    if (f.selector == approve(address, uint256).selector) {
        address spender_;
        uint256 amount;
        approve(e, spender_, amount);
        if (from == e.msg.sender && spender == spender_) {
            assert allowance(from, spender) == amount;
        } else {
            assert allowance(from, spender) == allowanceBefore;
        }
    } else if (f.selector == transferFrom(address,address,uint256).selector || f.selector == transferSharesFrom(address,address,uint256).selector) {
        address from_;
        address to;
        address amount;
        transferFrom(e, from_, to, amount);
        uint256 allowanceAfter = allowance(from, spender);
        if (from == from_ && spender == e.msg.sender) {
            assert from == to || allowanceBefore == max_uint256 || allowanceAfter == allowanceBefore - amount;
        } else {
            assert allowance(from, spender) == allowanceBefore;
        }
    } else if (f.selector == decreaseAllowance(address, uint256).selector) {
        address spender_;
        uint256 amount;
        require amount <= allowanceBefore;
        decreaseAllowance(e, spender_, amount);
        if (from == e.msg.sender && spender == spender_) {
            assert allowance(from, spender) == allowanceBefore - amount;
        } else {
            assert allowance(from, spender) == allowanceBefore;
        }
    } else if (f.selector == increaseAllowance(address, uint256).selector) {
        address spender_;
        uint256 amount;
        require amount + allowanceBefore < max_uint256;
        increaseAllowance(e, spender_, amount);
        if (from == e.msg.sender && spender == spender_) {
            assert allowance(from, spender) == allowanceBefore + amount;
        } else {
            assert allowance(from, spender) == allowanceBefore;
        }
    } else {
        calldataarg args;
        f(e, args);
        assert allowance(from, spender) == allowanceBefore;
    }
}

// /*
//     @Rule

//     @Description:
//         Transfer from a to b doesn't change the sum of their balances

//     @Notes:

//     @Link:

// */
// rule TransferSumOfFromAndToBalancesStaySame(address to, uint256 amount) {
//     env e;
//     mathint sum = balanceOf(e.msg.sender) + balanceOf(to);
//     require sum < max_uint256;
//     transfer(e, to, amount); 
//     assert balanceOf(e.msg.sender) + balanceOf(to) == sum;
// }

// /*
//     @Rule

//     @Description:
//         Transfer using transferFrom() from a to b doesn't change the sum of their balances


//     @Notes:

//     @Link:

// */
// rule TransferFromSumOfFromAndToBalancesStaySame(address from, address to, uint256 amount) {
//     env e;
//     mathint sum = balanceOf(from) + balanceOf(to);
//     require sum < max_uint256;
//     transferFrom(e, from, to, amount); 
//     assert balanceOf(from) + balanceOf(to) == sum;
// }

// /*
//     @Rule

//     @Description:
//         Transfer from msg.sender to alice doesn't change the balance of other addresses


//     @Notes:

//     @Link:

// */
// rule TransferDoesntChangeOtherBalance(address to, uint256 amount, address other) {
//     env e;
//     require other != e.msg.sender;
//     require other != to && other != currentContract;
//     uint256 balanceBefore = balanceOf(other);
//     transfer(e, to, amount); 
//     assert balanceBefore == balanceOf(other);
// }

// /*
//     @Rule

//     @Description:
//         Transfer from alice to bob using transferFrom doesn't change the balance of other addresses


//     @Notes:

//     @Link:

// */
// rule TransferFromDoesntChangeOtherBalance(address from, address to, uint256 amount, address other) {
//     env e;
//     require other != from;
//     require other != to;
//     uint256 balanceBefore = balanceOf(other);
//     transferFrom(e, from, to, amount); 
//     assert balanceBefore == balanceOf(other);
// }

// /*
//     @Rule

//     @Description:
//         Balance of an address, who is not a sender or a recipient in transfer functions, doesn't decrease 
//         as a result of contract calls


//     @Notes:
//         USDC token has functions like transferWithAuthorization that use a signed message for allowance. 
//         FTT token has a burnFrom that lets an approved spender to burn owner's token.
//         Certora prover finds these counterexamples to this rule.
//         In general, the rule will fail on all functions other than transfer/transferFrom that change a balance of an address.

//     @Link:

// */
// rule OtherBalanceOnlyGoesUp(address other, method f) {
//     env e;
//     require other != currentContract;
//     uint256 balanceBefore = balanceOf(other);

//     if (f.selector == transferFrom(address, address, uint256).selector) {
//         address from;
//         address to;
//         uint256 amount;
//         require(other != from);
//         require balanceOf(from) + balanceBefore < max_uint256;
//         transferFrom(e, from, to, amount);
//     } else if (f.selector == transfer(address, uint256).selector) {
//         require other != e.msg.sender;
//         require balanceOf(e.msg.sender) + balanceBefore < max_uint256;
//         calldataarg args;
//         f(e, args);
//     } else {
//         require other != e.msg.sender;
//         calldataarg args;
//         f(e, args);
//     }

//     assert balanceOf(other) >= balanceBefore;
// }

// rule sanity(method f)
// {
// 	env e;
// 	calldataarg arg;
// 	sinvoke f(e, arg);
// 	assert false;
// }
