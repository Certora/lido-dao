using HashConsensus as hashCon

methods {
    // HashConsensus dispatched methods
    getCurrentFrame() => DISPATCHER(true)
    getFrameConfig() => DISPATCHER(true)
    getChainConfig() => DISPATCHER(true)

    // LegacyOracle methods
    getBeaconSpec() returns (uint64,uint64,uint64,uint64)
    getLastCompletedReportDelta() returns (uint256,uint256,uint256) envfree
    
    // Summaries - addresses
    getApp(bytes32 a,bytes32 b) => getAppGhost(a, b)
    getScriptExecutor(bytes) => CONSTANT
    getRecoveryVault() => recoveryVaultAddress()
    getConsensusContract() => consensusContract()
    getAccountingOracle() => accountingAddress()
    accountingOracle() => accountingAddress()
    lido() => lidoAddress()
}

/**************************************************
 *             Methods definitions                *
 **************************************************/

definition isInitialize(method f) returns bool = 
    f.selector == initialize(address,address).selector;

definition isFinalize(method f) returns bool = 
    f.selector == finalizeUpgrade_v4(address).selector;

definition isHandleRebase(method f) returns bool = 
    f.selector == 
        handlePostTokenRebase(uint256,uint256,uint256,uint256,uint256,uint256,uint256).selector;

definition isHandleConsensus(method f) returns bool = 
    f.selector == handleConsensusLayerReport(uint256,uint256,uint256).selector;

definition externalChangingMethods(method f) returns bool = 
    isHandleRebase(f) || isHandleConsensus(f);

// Filtering functions that give me trouble but shouldn't.
definition customFilter(method f) returns bool = !(
    f.selector == canPerform(address,bytes32,uint256[]).selector ||
    f.selector == transferToVault(address).selector);

/**************************************************
 *             Beacon spec assumption             *
 **************************************************/

function nonZeroBeaconSpec(env e) returns bool {
    uint64 epochs1;
    uint64 slots1;
    uint64 seconds1;
    uint64 genesis1;
    epochs1, slots1, seconds1, genesis1 = getBeaconSpec(e);
    bool nonOverFlow = slots1 * seconds1 < (1 << 64);
    return (nonOverFlow &&
        epochs1 !=0 &&
        slots1 !=0 &&
        seconds1 !=0 &&
        genesis1 !=0);
}

/**************************************************
 *          Contracts addresses ghosts            *
 **************************************************/

ghost consensusContract() returns address {
    axiom consensusContract() == hashCon;
}

ghost accountingAddress() returns address {
    axiom accountingAddress() != 0;
    axiom accountingAddress() != currentContract;
    axiom accountingAddress() != hashCon;
}

ghost lidoAddress() returns address {
    axiom lidoAddress() != 0;
    axiom lidoAddress() != currentContract;
    axiom lidoAddress() != hashCon;
}

ghost recoveryVaultAddress() returns address {
    axiom recoveryVaultAddress() != 0;
    axiom recoveryVaultAddress() != currentContract;
    axiom recoveryVaultAddress() != hashCon;
}

ghost getAppGhost(bytes32, bytes32) returns address {
    axiom forall bytes32 a . forall bytes32 b . 
        getAppGhost(a, b) != 0 && 
        getAppGhost(a, b) != currentContract &&
        getAppGhost(a, b) != hashCon;
}

/**************************************************
 *              Beacpn Spec Rules                 *
 **************************************************/

rule beaconSpecChangedOnlyByInitialize(method f) 
filtered{f -> customFilter(f)} {
    env e1;
    env e2; calldataarg args;
    env e3;
    uint64 epochs1;
    uint64 slots1;
    uint64 seconds1;
    uint64 genesis1;
    epochs1, slots1, seconds1, genesis1 = getBeaconSpec(e1);
    
        f(e2, args);

    if(isInitialize(f)) {
        assert nonZeroBeaconSpec(e3), "One of the chain specs is set to zero";
    }
    uint64 epochs2;
    uint64 slots2;
    uint64 seconds2;
    uint64 genesis2;
    epochs2, slots2, seconds2, genesis2 = getBeaconSpec(e3);
    
    assert !(
        epochs1 == epochs2 &&
        slots1 == slots2 &&
        seconds1 == seconds2 &&
        genesis1 == genesis2) => isInitialize(f), 
        "The chain spec is changed by another method"; 
}

rule reportDeltaChangedOnlyByReport(method f) 
filtered{f -> customFilter(f)} {
    env e;
    calldataarg args;
    
    uint256 postEth_before;
    uint256 preEth_before;
    uint256 timeElapsed_before; 
    postEth_before, preEth_before, timeElapsed_before = 
        getLastCompletedReportDelta();
    
    f(e, args);

    uint256 postEth_after;
    uint256 preEth_after;
    uint256 timeElapsed_after; 
    postEth_after, preEth_after, timeElapsed_after = 
        getLastCompletedReportDelta();

    assert !(
        postEth_before == postEth_after &&
        preEth_before == preEth_after &&
        timeElapsed_before == timeElapsed_after) => isHandleRebase(f),
        "The report data is changed by another method";
}

rule viewFunctionsDontRevertPostFinalize(method f) 
filtered{f -> f.isView && customFilter(f)} {
    env e1;
    env e2;
    calldataarg args1;
    calldataarg args2;
    finalizeUpgrade_v4(e1, args1);
    require nonZeroBeaconSpec(e1);

    require e2.msg.value == 0;
    require e2.block.timestamp < to_uint256(1 << 32);
    f@withrevert(e2, args2);
    assert !lastReverted;
}

rule viewFunctionsDontRevertPreserve(method f, method g) 
filtered{f -> f.isView && customFilter(f), g -> externalChangingMethods(g)} {
    env e1;
    env e2;
    env e3;
    calldataarg args1;
    calldataarg args2;
    calldataarg args3;
    require nonZeroBeaconSpec(e1);

    f(e1, args1);
    g(e2, args2);

    require e3.msg.value == e1.msg.value;
    require e3.block.timestamp < to_uint256(1 << 32);
    f@withrevert(e3, args3);
    assert !lastReverted;
}

/**************************************************
 *                   MISC Rules                   *
 **************************************************/

rule cannotInitializeTwice(method f)
filtered{f -> !isInitialize(f)} {
    env e1;
    env e2;
    env e3;
    calldataarg args1;
    calldataarg args2;
    calldataarg args3;
    initialize(e1, args1);
    f@withrevert(e2, args2);
    initialize@withrevert(e3, args3);

    assert lastReverted;
}

rule cannotFinalizeTwice(method f)
filtered{f -> !isFinalize(f)} {
    env e1;
    env e2;
    env e3;
    calldataarg args1;
    calldataarg args2;
    calldataarg args3;
    finalizeUpgrade_v4(e1, args1);
    f@withrevert(e2, args2);
    finalizeUpgrade_v4@withrevert(e3, args3);

    assert lastReverted;
}
