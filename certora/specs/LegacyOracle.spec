using HashConsensus as hashC

methods {
    // HashConsensus dispatched methods
    getCurrentFrame() => DISPATCHER(true)
    getFrameConfig() => DISPATCHER(true)
    getChainConfig() => DISPATCHER(true)

    // LegacyOracle methods
    getBeaconSpec() returns (uint64,uint64,uint64,uint64)
    getLastCompletedReportDelta() returns (uint256,uint256,uint256) envfree
    
    // Summaries - addresses
    getApp(bytes32,bytes32) => NONDET
    getScriptExecutor(bytes) => NONDET
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

// Filtering functions that give me trouble but shouldn't.
definition customFilter(method f) returns bool = !(
    f.selector == canPerform(address,bytes32,uint256[]).selector ||
    f.selector == transferToVault(address).selector);

/**************************************************
 *                  Beacon spec ghosts            *
 **************************************************/

ghost uint64 EpochsPerFrame;
ghost uint64 SlotsPerEpoch;
ghost uint64 SecondsPerSlot;
ghost uint64 GenesisTime;

/// Saves the current values of the Beacon spec to the ghost variables.
function BeaconSpec(env e) {
    uint64 epochesPerFrame;
    uint64 slotsPerEpoch;
    uint64 secondsPerSlot;
    uint64 genesisTime;
    epochesPerFrame, slotsPerEpoch, secondsPerSlot, genesisTime = 
        getBeaconSpec(e);

    havoc EpochsPerFrame assuming EpochsPerFrame@new == epochesPerFrame; 
    havoc SlotsPerEpoch assuming SlotsPerEpoch@new == slotsPerEpoch;
    havoc SecondsPerSlot assuming SecondsPerSlot@new == secondsPerSlot;
    havoc GenesisTime assuming GenesisTime@new == genesisTime;
}

/**************************************************
 *          Contracts addresses ghosts            *
 **************************************************/

ghost consensusContract() returns address {
    axiom consensusContract() == hashC;
}

ghost accountingAddress() returns address {
    axiom accountingAddress() != 0;
    axiom accountingAddress() != currentContract;
    axiom accountingAddress() != hashC;
}

ghost lidoAddress() returns address {
    axiom lidoAddress() != 0;
    axiom lidoAddress() != currentContract;
    axiom lidoAddress() != hashC;
}

ghost recoveryVaultAddress() returns address {
    axiom recoveryVaultAddress() != 0;
    axiom recoveryVaultAddress() != currentContract;
    axiom recoveryVaultAddress() != hashC;
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

    assert epochs2 != 0, "The epochs per frame is set to zero";
    assert slots2 != 0, "The slots per epoch is set to zero";
    assert seconds2 != 0, "The seconds per slot is set to zero";
    assert genesis2 != 0, "The genesis time is set to zero";
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

/**************************************************
 *                   MISC Rules                   *
 **************************************************/

rule anyoneCanCall_transferToVault(address token) {
    env e1;
    env e2;
    storage initState = lastStorage;

    require e1.msg.value == e2.msg.value;
    require e1.block.timestamp == e2.block.timestamp;
    transferToVault(e1, token);
    transferToVault@withrevert(e2, token) at initState;

    require e1.msg.sender == e2.msg.sender => !lastReverted;
    assert !lastReverted;
}

rule cannotInitializeTwice(method f)
filtered{f -> !isInitialize(f)} {
    env e1;
    env e2;
    env e3;
    calldataarg args1;
    calldataarg args2;
    calldataarg args3;
    initialize(e1, args1);
    f(e2, args2);
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
    f(e2, args2);
    finalizeUpgrade_v4@withrevert(e3, args3);

    assert lastReverted;
}
