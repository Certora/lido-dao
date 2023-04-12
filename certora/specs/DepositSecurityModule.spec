using LidoLocator as Locator
using DepositSecurityModuleHarness as DSM
using StakingRouter as StkRouter
using Lido as Lido
// using DepositContract as DepositContract

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

    // BeaconChainDepositor.sol
    // havoc - "all contracts"
        // _computeDepositDataRoot(bytes, bytes, bytes) returns(bytes32) => DISPATCHER(true)       // DISPATCHER wasn't applied

    // NodeOperatorsRegistry.sol
    // havoc - "all contracts"
        obtainDepositData(uint256, bytes) returns(bytes, bytes) => DISPATCHER(true)             // DISPATCHER wasn't applied

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
    getSortedGuardianSignaturesLength() returns(uint256) envfree

    LIDO() returns(address) envfree
    PAUSE_MESSAGE_PREFIX() returns(bytes32) envfree

    recover(bytes32 hash, bytes32 r, bytes32 vs) returns(address) => recoverGhostCVL(hash, r, vs)

    getKeccak256(uint256, uint256) returns(bytes32) envfree
}


/**************************************************
 *                   DEFINITIONS                  *
 **************************************************/

// removig harness functions from f method calls
definition excludeMethods(method f) returns bool =
    f.selector != depositBufferedEtherCall(uint256, bytes32, bytes32, uint256, uint256, bytes).selector
        && f.selector != _verifySignaturesCall(bytes32,uint256,bytes32,uint256,uint256,(bytes32,bytes32),(bytes32,bytes32)).selector;



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


function recoverGhostCVL(bytes32 hash, bytes32 r, bytes32 vs) returns address {
    requireInvariant uniqueRecoverGhost();
    return recoveryGhostSingle[hash][r][vs];
}



/**************************************************
 *               GHOSTS AND HOOKS                 *
 **************************************************/


// ghost mapping(address => uint256) guardianIndicesOneBasedMirror {
//     init_state axiom forall address a. guardianIndicesOneBasedMirror[a] == 0;
// }

// hook Sstore guardianIndicesOneBased[KEY address guardian] uint256 index
//     (uint256 old_index) STORAGE
// {
//     guardianIndicesOneBasedMirror[guardian] = index;
// }

// hook Sload uint256 index guardianIndicesOneBased[KEY address guardian]  STORAGE {
//     require guardianIndicesOneBasedMirror[guardian] == index;
// }


// ghost mapping(uint256 => address) guardiansMirror {
//     init_state axiom forall uint256 a. guardiansMirror[a] == 0;
// }

// hook Sstore guardians[INDEX uint256 index] address guardian
//     (address old_guardian) STORAGE
// {
//     guardiansMirror[index] = guardian;
// }

// hook Sload address guardian guardians[INDEX uint256 index]  STORAGE {
//     require guardiansMirror[index] == guardian;
// }


// ghost uint256 mirrorArrayLen {
//     init_state axiom mirrorArrayLen == 0;
//     axiom mirrorArrayLen != max_uint256; 
// }

// hook Sstore guardians.(offset 0) uint256 newLen 
//     (uint256 oldLen) STORAGE {
//     mirrorArrayLen = newLen;
// }

// hook Sload uint256 len guardians.(offset 0) STORAGE {
//     require mirrorArrayLen == len;
// }


ghost mapping(bytes32 => mapping(bytes32 => mapping(bytes32 => address))) recoveryGhostSingle;

// STATUS - fails instate but it still can be used for function summarization
// https://prover.certora.com/output/3106/ed233ee8cb494510af91b32f3c474fd4/?anonymousKey=091aa8d9f007189639987c57abd55e51898d8390
invariant uniqueRecoverGhost()
    forall bytes32 hash1. forall bytes32 r1. forall bytes32 vs1. 
    forall bytes32 hash2. forall bytes32 r2. forall bytes32 vs2.
        hash1 != hash2 || r1 != r2 || vs1 != vs2 <=> 
            recoveryGhostSingle[hash1][r1][vs1] != recoveryGhostSingle[hash2][r2][vs2]



/**************************************************
 *                    VERIFIED                    *
 **************************************************/

// STATUS - verified
// Only owner can change owner and only via setOwner()
rule onlyOwnerCanChangeOwner(env e, method f) filtered { f -> excludeMethods(f) } {
    address ownerBefore = getOwner();

    calldataarg args;
    f(e, args);

    address ownerAfter = getOwner();

    assert ownerBefore != ownerAfter 
            => (ownerBefore == e.msg.sender
                && f.selector == setOwner(address).selector);
}


// STATUS - verified
// Only owner can change pauseIntentValidityPeriodBlocks and only via setPauseIntentValidityPeriodBlocks()
rule onlyOwnerCanChangePauseIntentValidityPeriodBlocks(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 validityBefore = getPauseIntentValidityPeriodBlocks();

    calldataarg args;
    f(e, args);

    uint256 vaidityAfter = getPauseIntentValidityPeriodBlocks();

    assert validityBefore != vaidityAfter 
            => (getOwner() == e.msg.sender
                && f.selector == setPauseIntentValidityPeriodBlocks(uint256).selector);
}


// STATUS - verified
// Only owner can change maxDepositsPerBlock and only via setMaxDeposits()
rule onlyOwnerCanChangeMaxDepositsPerBlock(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 maxDepositBefore = getMaxDeposits();

    calldataarg args;
    f(e, args);

    uint256 maxDepositAfter = getMaxDeposits();

    assert maxDepositBefore != maxDepositAfter 
            => (getOwner() == e.msg.sender
                && f.selector == setMaxDeposits(uint256).selector);
}


// STATUS - verified
// Only owner can change minDepositBlockDistance and only via setMinDepositBlockDistance()
rule onlyOwnerCanChangeMinDepositBlockDistance(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 minDepositBlockDistanceBefore = getMinDepositBlockDistance();

    calldataarg args;
    f(e, args);

    uint256 minDepositBlockDistanceAfter = getMinDepositBlockDistance();

    assert minDepositBlockDistanceBefore != minDepositBlockDistanceAfter 
            => (getOwner() == e.msg.sender
                && f.selector == setMinDepositBlockDistance(uint256).selector);
}


// STATUS - verified
// Only owner can change quorum and only via setGuardianQuorum(), addGuardian(), addGuardians(), removeGuardian()
rule onlyOwnerCanChangeQuorum(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 quorumBefore = getGuardianQuorum();

    calldataarg args;
    f(e, args);

    uint256 quorumAfter = getGuardianQuorum();

    assert quorumBefore != quorumAfter 
            => (getOwner() == e.msg.sender
                && (f.selector == setGuardianQuorum(uint256).selector
                    || f.selector == addGuardian(address, uint256).selector
                    || f.selector == addGuardians(address[], uint256).selector
                    || f.selector == removeGuardian(address, uint256).selector));
}


// STATUS - verified (needs to be run without ghosts: HOOK_INLINING issue)
// Only owner can add/remove guardians and only via addGuardian(), addGuardians(), removeGuardian()
rule onlyOwnerCanChangeGuardians(env e, method f) filtered { f -> excludeMethods(f) } {
    int256 lengthBefore = getGuardiansLength();

    calldataarg args;
    f(e, args);

    int256 lengthAfter = getGuardiansLength();

    assert lengthBefore != lengthAfter 
            => (getOwner() == e.msg.sender
                && (f.selector == addGuardian(address, uint256).selector
                    || f.selector == addGuardians(address[], uint256).selector
                    || f.selector == removeGuardian(address, uint256).selector));
}


// STATUS - verified
// Only owner can unpause deposits and only via unpauseDeposits()
rule onlyOwnerCanChangeUnpause(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 _stakingModuleId;

    uint256 pausedBefore = StkRouter.getStakingModuleStatus(_stakingModuleId);

    calldataarg args;
    f(e, args);

    assert (pausedBefore == 1 
                && StkRouter.getStakingModuleStatus(_stakingModuleId) == 0)
            => (getOwner() == e.msg.sender
                && f.selector == unpauseDeposits(uint256).selector);
}


// STATUS - verified
// If stakingModuleId was paused, can unpause
rule canUnpause(env e, env e2) {
    uint256 blockNumber;
    uint256 stakingModuleId;
    DSM.Signature sig;

    uint256 pausedBefore = StkRouter.getStakingModuleStatus(stakingModuleId);

    unpauseDeposits(e2, stakingModuleId);

    assert pausedBefore == 1 => StkRouter.getStakingModuleStatus(stakingModuleId) == 0, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// It's impossible to stop deposits from DepositSecurityModule.sol
invariant cantStop(uint256 stakingModuleId)
    StkRouter.getStakingModuleStatus(stakingModuleId) != 2
    filtered { f -> excludeMethods(f) }


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
// guardians array can't contain the same guardian twice. guardians array and guardianIndicesOneBased mapping are correlated
// invariant unique()
//     (forall address guardian1.
//         forall address guardian2.
//             (guardian1 != guardian2
//             => (guardianIndicesOneBasedMirror[guardian1] != guardianIndicesOneBasedMirror[guardian2]
//                 || guardianIndicesOneBasedMirror[guardian1] == 0))
//             && guardianIndicesOneBasedMirror[guardian1] <= mirrorArrayLen)
//     && (forall uint256 i. i < mirrorArrayLen => (guardianIndicesOneBasedMirror[guardiansMirror[i]] - 1) == i)
//     filtered { f -> excludeMethods(f) }
//     {
//         preserved {
//             require mirrorArrayLen < max_uint128;   // very long array causes false violations
//         }
//     }


// STATUS - verified
// Zero address can't be a guardian
// invariant zeroIsNotGuardian()
//     !isGuardian(0)
//     filtered { f -> excludeMethods(f) }
//     {
//         preserved {
//             require mirrorArrayLen < max_uint128;   // very long array causes false violations
//             requireInvariant unique();      // need it to synchronize array and mapping
//         }
//     }


// STATUS - verified
// Checking signatures: can't pass the same guardian signature twice in _verifySignaturesCall()
rule youShallNotPassTwice(env e) {
    bytes32 depositRoot;
    uint256 blockNumber;
    bytes32 blockHash;
    uint256 stakingModuleId;
    uint256 nonce;
    DSM.Signature sig1;
    DSM.Signature sig2;

    _verifySignaturesCall@withrevert(e,
        depositRoot,
        blockNumber,
        blockHash,
        stakingModuleId,
        nonce,
        sig1,
        sig2
    );

    bool isReverted = lastReverted;
    
    assert compareSignatures(e, sig1, sig2) => isReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// Checking signatures: can't pass a signature of non-guardian
rule nonGuardianCantSign(env e) {
    bytes32 depositRoot;
    uint256 blockNumber;
    bytes32 blockHash;
    uint256 stakingModuleId;
    uint256 nonce;
    DSM.Signature sig1;
    DSM.Signature sig2;

    address addressFromSig1 = getAddressForSignature(e, depositRoot, blockNumber, blockHash, stakingModuleId, nonce, sig1);
    address addressFromSig2 = getAddressForSignature(e, depositRoot, blockNumber, blockHash, stakingModuleId, nonce, sig2);

    _verifySignaturesCall@withrevert(e,
        depositRoot,
        blockNumber,
        blockHash,
        stakingModuleId,
        nonce,
        sig1,
        sig2
    );

    bool isReverted = lastReverted;
    
    assert !isGuardian(addressFromSig1) || !isGuardian(addressFromSig2) => isReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - verified (needs to be run without ghosts: HOOK_INLINING issue)
// If canDeposit() returns false/reverts, depositBufferedEther() reverts
rule agreedRevertsSimple(env e) {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;

    bool isDepositable = canDeposit@withrevert(e, stakingModuleId);
    bool isCanDepositReverted = lastReverted;

    depositBufferedEtherCall@withrevert(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );
    bool isDepositReverted = lastReverted;

    assert (isCanDepositReverted || !isDepositable) => isDepositReverted;
}


// STATUS - verified
// Only guardian can pause deposits
// rule onlyGuardianCanPause(env e, method f) filtered { f -> excludeMethods(f) } {
//     uint256 blockNumber;
//     uint256 stakingModuleId;
//     DSM.Signature sig;
//     bytes32 checking = PAUSE_MESSAGE_PREFIX();

//     require mirrorArrayLen <= max_uint256 / 2;  // very long array causes false violations
//     requireInvariant unique();                  // need it to synchronize array and mapping to avoid over/underflows
//     require StkRouter.getStakingModuleStatus(stakingModuleId) == 0;

//     bytes32 keccakCheckVarBefore = getKeccak256(blockNumber, stakingModuleId);

//     pauseHelper(f, e, blockNumber, stakingModuleId, sig);

//     bytes32 keccakCheckVarAfter = getKeccak256(blockNumber, stakingModuleId);

//     assert StkRouter.getStakingModuleStatus(stakingModuleId) == 1 
//             => 
//             ((getGuardianIndex(e.msg.sender) >= to_int256(0)
//                     || getGuardianIndex(getHashedAddress(blockNumber, stakingModuleId, sig)) >= to_int256(0))
//                 && f.selector == pauseDeposits(uint256,uint256,(bytes32,bytes32)).selector), "Remember, with great power comes great responsibility.";
// }


/**************************************************
 *                   IN PROGRESS                  *
 **************************************************/


// STATUS - tool errors (doesn't make sense to implement with code simplifications)
// can't deposit with the same input twice
// rule cannotDepositTwice(env e, method f) {
//     uint256 blockNumber;
//     bytes32 blockHash;
//     bytes32 depositRoot;
//     uint256 stakingModuleId;
//     uint256 nonce;
//     bytes depositCalldata;
    
//     uint256 before = getEthBalance(Lido);

//     depositBufferedEtherCall(e,
//         blockNumber,
//         blockHash,
//         depositRoot,
//         stakingModuleId,
//         nonce,
//         depositCalldata
//     );

//     uint256 after = getEthBalance(Lido);

//     depositBufferedEtherCall@withrevert(e,
//         blockNumber,
//         blockHash,
//         depositRoot,
//         stakingModuleId,
//         nonce,
//         depositCalldata
//     );

//     bool isReverted = lastReverted;

//     assert (before - 32 == after) => isReverted, "Remember, with great power comes great responsibility.";
// }




// STATUS - tool errors (doesn't make sense to implement with code simplifications)
// checking depositBufferedEther 5/6 conditions from doc:
/*
     * Reverts if any of the following is true:
     *   1. IDepositContract.get_deposit_root() != depositRoot.
     *   2. StakingModule.getNonce() != nonce.
     *   3. The number of guardian signatures is less than getGuardianQuorum().
     *   4. An invalid or non-guardian signature received.   // check in another rule
     *   5. block.number - StakingModule.getLastDepositBlock() < minDepositBlockDistance.
     *   6. blockhash(blockNumber) != blockHash.
     */
// rule revert5(env e, env e2, method f) {
//     uint256 blockNumber;
//     bytes32 blockHash;
//     bytes32 depositRoot;
//     uint256 stakingModuleId;
//     uint256 nonce;
//     bytes depositCalldata;

//     // bytes32 getDepositRootBefore = DepositContract.get_deposit_root(e);
//     uint256 signaturesLengthBefore = getSortedGuardianSignaturesLength();
//     uint256 nonceBefore = StkRouter.getStakingModuleNonce(e, stakingModuleId);
//     uint256 quorumBefore = getGuardianQuorum();
//     uint256 getStakingModuleLastDepositBlockBefore = StkRouter.getStakingModuleLastDepositBlock(e, stakingModuleId);
//     uint256 minDepositBlockDistanceBefore = getMinDepositBlockDistance();
//     bytes32 blockHashBefore = returnBlockHash(e, blockNumber);

//     require e.block.number == e2.block.number;

//     depositBufferedEtherCall@withrevert(e2,
//         blockNumber,
//         blockHash,
//         depositRoot,
//         stakingModuleId,
//         nonce,
//         depositCalldata
//     );

//     bool isReverted = lastReverted;

//     assert // getDepositRootBefore != depositRoot   // deposit_contract is too heavy, need a workaround
//                 // || 
//                 nonceBefore != nonce
//                 || signaturesLengthBefore < quorumBefore
//                 || to_uint256(e2.block.number - getStakingModuleLastDepositBlockBefore) < minDepositBlockDistanceBefore
//                 || blockHashBefore != blockHash || blockHash == 0
//             => isReverted, "Remember, with great power comes great responsibility.";
// }




// STATUS - tool errors (doesn't make sense to implement with code simplifications)
// After calling depositBufferedEther check that nonce was increased by 1
// rule noncePlusOne(env e, method f) {
//     uint256 blockNumber;
//     bytes32 blockHash;
//     bytes32 depositRoot;
//     uint256 stakingModuleId;
//     uint256 nonce;
//     bytes depositCalldata;
    
//     uint256 nonceBefore = StkRouter.getStakingModuleNonce(e, stakingModuleId);

//     depositBufferedEtherCall(e,
//         blockNumber,
//         blockHash,
//         depositRoot,
//         stakingModuleId,
//         nonce,
//         depositCalldata
//     );

//     uint256 nonceAfter = StkRouter.getStakingModuleNonce(e, stakingModuleId);

//     assert to_uint256(nonceBefore + 1) == nonceAfter, "Remember, with great power comes great responsibility.";
// }
