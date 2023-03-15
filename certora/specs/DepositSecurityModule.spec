using LidoLocator as Locator
using DepositSecurityModuleHarness as DSM
using StakingRouter as StkRouter
using ECDSA as SigContact

methods {
    // StakingRouter.sol
    // havoc - "all contracts"
        pauseStakingModule(uint256) => DISPATCHER(true)
        resumeStakingModule(uint256) => DISPATCHER(true)
        getStakingModuleMaxDepositsCount(uint256, uint256) returns(uint256) => DISPATCHER(true)
    // havoc - "only the return value"
        getStakingModuleIsActive(uint256) returns(bool) => DISPATCHER(true)
        getStakingModuleLastDepositBlock(uint256) returns(uint256) => DISPATCHER(true)
        getStakingModuleIsDepositsPaused(uint256) returns(bool) => DISPATCHER(true)
        getStakingModuleNonce(uint256) returns(uint256) => DISPATCHER(true)
    // envfree
        StkRouter.getStakingModuleStatus(uint256) returns(uint8) envfree

    // Lido.sol
    // havoc - "all contracts"
        deposit(uint256, uint256, bytes) => DISPATCHER(true)
    // havoc - "only the return value"
        canDeposit() returns(bool) => DISPATCHER(true)

    // WithdrawalQueueHarness.sol
    // havoc - "all contracts"
        unfinalizedStETH() returns(uint256) => DISPATCHER(true)

    // LidoLocator.sol
    // havoc - "all contracts"
        stakingRouter() returns(address) => DISPATCHER(true)
        isBunkerModeActive() returns(bool) => DISPATCHER(true)
        withdrawalQueue() returns(address) => DISPATCHER(true)
        depositSecurityModule() returns(address) => DISPATCHER(true)

    // DepositContractMock.sol
    // havoc - "only the return value"
        get_deposit_root() returns(bytes32) => NONDET // DISPATCHER(true)

    // StakingModuleMock.sol
    // havoc - "only the return value"
        getStakingModuleSummary() returns(uint256, uint256, uint256) => DISPATCHER(true)
        getNonce() returns (uint256) => DISPATCHER(true)
        obtainDepositData(uint256, bytes) => DISPATCHER(true)


    // DepositSecurityModule.sol
    guardianIndicesOneBased(address) returns(uint256) envfree
    getGuardian(uint256) returns(address) envfree
    getGuardianIndex(address) returns(int256) envfree
    getGuardiansLength() returns(int256) envfree
    getOwner() returns(address) envfree
    getPauseIntentValidityPeriodBlocks() returns(uint256) envfree
    getMaxDeposits() returns(uint256) envfree
    getMinDepositBlockDistance() returns(uint256) envfree
    getGuardianQuorum() returns(uint256) envfree
    isGuardian(address) returns(bool) envfree
    getHashedAddress(uint256,uint256,(bytes32,bytes32)) returns(address) envfree
    getEthBalance(address) returns(uint256) envfree
}



rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}



/**************************************************
 *                   DEFINITIONS                  *
 **************************************************/

definition excludeMethods(method f) returns bool =
    f.selector != depositBufferedEtherCall(uint256, bytes32, bytes32, uint256, uint256, bytes).selector;



/**************************************************
 *                    FUNCTIONS                   *
 **************************************************/


function pauseHelper(method f, env e, uint256 blockNumber, uint256 stakingModuleId, DSM.Signature sig) {
    if (f.selector == pauseDeposits(uint256,uint256,(bytes32,bytes32)).selector){ 
        pauseDeposits(e, blockNumber, stakingModuleId, sig);
    } else {
        calldataarg args;
        f(e, args);
    }
}



/**************************************************
 *               GHOSTS AND HOOKS                 *
 **************************************************/


ghost mapping(address => uint256) guardianIndicesOneBasedMirror {
    init_state axiom forall address a. guardianIndicesOneBasedMirror[a] == 0;
}

hook Sstore guardianIndicesOneBased[KEY address guardian] uint256 index
    (uint256 old_index) STORAGE
{
    guardianIndicesOneBasedMirror[guardian] = index;
}

hook Sload uint256 index guardianIndicesOneBased[KEY address guardian]  STORAGE {
    require guardianIndicesOneBasedMirror[guardian] == index;
}


ghost mapping(uint256 => address) guardiansMirror {
    init_state axiom forall uint256 a. guardiansMirror[a] == 0;
}

hook Sstore guardians[INDEX uint256 index] address guardian
    (address old_guardian) STORAGE
{
    guardiansMirror[index] = guardian;
}

hook Sload address guardian guardians[INDEX uint256 index]  STORAGE {
    require guardiansMirror[index] == guardian;
}


ghost uint256 mirrorArrayLen {
    init_state axiom mirrorArrayLen == 0;
    axiom mirrorArrayLen != max_uint256; 
}

hook Sstore guardians.(offset 0) uint256 newLen 
    (uint256 oldLen) STORAGE {
    mirrorArrayLen = newLen;
}

hook Sload uint256 len guardians.(offset 0) STORAGE {
    require mirrorArrayLen == len;
}



/**************************************************
 *                    VERIFIED                    *
 **************************************************/

// onlyOwner can change owner, pauseIntentValidityPeriodBlocks, maxDepositsPerBlock, minDepositBlockDistance, quorum; add/remove guardians, unpause deposits
// STATUS - verified
rule onlyOwnerCanChangeOwner(env e, method f) {
    address ownerBefore = getOwner();

    calldataarg args;
    f(e, args);

    address ownerAfter = getOwner();

    assert ownerBefore != ownerAfter => ownerBefore == e.msg.sender, "Remember, with great power comes great responsibility.";
}

// STATUS - verified
rule onlyOwnerCanChangePauseIntentValidityPeriodBlocks(env e, method f) {
    uint256 validityBefore = getPauseIntentValidityPeriodBlocks();

    calldataarg args;
    f(e, args);

    uint256 vaidityAfter = getPauseIntentValidityPeriodBlocks();

    assert validityBefore != vaidityAfter => getOwner() == e.msg.sender, "Remember, with great power comes great responsibility.";
}

// STATUS - verified
rule onlyOwnerCanChangeMaxDepositsPerBlock(env e, method f) {
    uint256 maxDepositBefore = getMaxDeposits();

    calldataarg args;
    f(e, args);

    uint256 maxDepositAfter = getMaxDeposits();

    assert maxDepositBefore != maxDepositAfter => getOwner() == e.msg.sender, "Remember, with great power comes great responsibility.";
}

// STATUS - verified
rule onlyOwnerCanChangeMinDepositBlockDistance(env e, method f) {
    uint256 minDepositBlockDistanceBefore = getMinDepositBlockDistance();

    calldataarg args;
    f(e, args);

    uint256 minDepositBlockDistanceAfter = getMinDepositBlockDistance();

    assert minDepositBlockDistanceBefore != minDepositBlockDistanceAfter => getOwner() == e.msg.sender, "Remember, with great power comes great responsibility.";
}

// STATUS - verified
rule onlyOwnerCanChangeQuorum(env e, method f) {
    uint256 quorumBefore = getGuardianQuorum();

    calldataarg args;
    f(e, args);

    uint256 quorumAfter = getGuardianQuorum();

    assert quorumBefore != quorumAfter => getOwner() == e.msg.sender, "Remember, with great power comes great responsibility.";
}

// STATUS - verified
rule onlyOwnerCanChangeGuardians(env e, method f) {
    int256 lengthBefore = getGuardiansLength();

    calldataarg args;
    f(e, args);

    int256 lengthAfter = getGuardiansLength();

    assert lengthBefore != lengthAfter => getOwner() == e.msg.sender, "Remember, with great power comes great responsibility.";
}

// STATUS - verified, except harness deposit call becuase deispatcher doesn't work: https://vaas-stg.certora.com/output/3106/0c772543a4c840acbd1c2a99d3b0d4a0/?anonymousKey=a1d7e728c263f2eb9efe1da3312eb9011b8cd538
rule onlyOwnerCanChangeUnpause(env e, method f) {
    uint256 _stakingModuleId;

    require StkRouter.getStakingModuleStatus(_stakingModuleId) == 1;

    calldataarg args;
    f(e, args);

    assert StkRouter.getStakingModuleStatus(_stakingModuleId) == 0 => getOwner() == e.msg.sender, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// if stakingModuleId is paused, can unpause
rule canUnpauseScenario(env e, env e2) {
    uint256 blockNumber;
    uint256 stakingModuleId;
    DSM.Signature sig;

    pauseDeposits(e, blockNumber, stakingModuleId, sig);

    unpauseDeposits@withrevert(e2, stakingModuleId);

    assert (getOwner() == e2.msg.sender
                && e2.msg.value == 0)
            => !lastReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// impossible to stop from here
rule cantStop(env e, method f) {
    uint256 stakingModuleId;
    uint8 stakingModuleStatusBefore = StkRouter.getStakingModuleStatus(stakingModuleId);

    calldataarg args;
    f(e, args);

    assert stakingModuleStatusBefore != 2 => StkRouter.getStakingModuleStatus(stakingModuleId) != 2, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// If stakingModuleId is paused, canDeposit() returns false
rule cannotDepositDuringPauseBool(env e) {
    uint256 stakingModuleId;

    uint8 stakingModuleStatus = StkRouter.getStakingModuleStatus(stakingModuleId);

    bool canDepos = canDeposit(e, stakingModuleId);

    assert stakingModuleStatus == 1 => !canDepos, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// If stakingModuleId is paused, depositBufferedEther() reverts
rule cannotDepositDuringPauseRevert(env e) {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;

    uint8 stakingModuleStatus = StkRouter.getStakingModuleStatus(stakingModuleId);

    depositBufferedEtherCall@withrevert(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    assert stakingModuleStatus == 1 => lastReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
invariant unique()
    (forall address guardian1.
        forall address guardian2.
            (guardian1 != guardian2
            => (guardianIndicesOneBasedMirror[guardian1] != guardianIndicesOneBasedMirror[guardian2]
                || guardianIndicesOneBasedMirror[guardian1] == 0))
            && guardianIndicesOneBasedMirror[guardian1] <= mirrorArrayLen)
    && (forall uint256 i. i < mirrorArrayLen => (guardianIndicesOneBasedMirror[guardiansMirror[i]] - 1) == i)
    filtered { f -> excludeMethods(f) }
    {
        preserved {
            require mirrorArrayLen < max_uint128;   // high numbers cause false violations 
        }
    }


// 0 can't be a guardian
// STATUS - verify
invariant zeroIsNotGuardian()
    !isGuardian(0)
    {
        preserved {
            require mirrorArrayLen < max_uint128;
            requireInvariant unique();  // need it to synchronize array and mapping
        }
    }


/**************************************************
 *                   IN PROGRESS                  *
 **************************************************/


// only guardian can pause deposits
// STATUS - in progress: https://vaas-stg.certora.com/output/3106/7f9fb82c59374a3d8a8c0c31b98ec44c/?anonymousKey=e8037a9854892fd6131b4f61605eea484994cdd3
// There can be 2 issues:
// 1. Hashing doesn't work properly.
// 2. need correlation invariant becuase array and mapping aren't synced. However, pauseDeposits() uses mapping indexes, while I use array
rule onlyGuardianCanPause(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 blockNumber;
    uint256 stakingModuleId;
    DSM.Signature sig;

    // requireInvariant unique();  // need it to synchronize array and mapping

    require StkRouter.getStakingModuleStatus(stakingModuleId) == 0;

    pauseHelper(f, e, blockNumber, stakingModuleId, sig);

    assert StkRouter.getStakingModuleStatus(stakingModuleId) == 1 
            => 
            ((isGuardian(e.msg.sender)
                    || isGuardian(getHashedAddress(blockNumber, stakingModuleId, sig)))
                && f.selector == pauseDeposits(uint256,uint256,(bytes32,bytes32)).selector), "Remember, with great power comes great responsibility.";
}


// STATUS - violated - possible deposit twice. is it intended? 
// can't deposit with the same input twice
rule cannotDepositTwice(env e, method f) {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;
    
    depositBufferedEtherCall(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    depositBufferedEtherCall@withrevert(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    assert lastReverted, "Remember, with great power comes great responsibility.";
}

rule whoChangedBalanceOf(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;

    uint256 before = getEthBalance(StkRouter);
    
    depositBufferedEtherCall(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    assert getEthBalance(StkRouter) == before, "balanceOf changed";
}

//-----IDEAS-----
// if canDeposit reverts, deposit reverts too
// if canDeposit doesn't revert, deposit doesn't revert too

// checking signatures (Merkle tree (kind of)) in _verifySignatures(). do we have an example?




// Note: check unstructuredStorage library