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
        // get_deposit_root() returns(bytes32) => NONDET // DISPATCHER(true)    

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
}

rule sanity(env e, method f) filtered { f -> excludeMethods(f) } {
    calldataarg args;
    f(e, args);
    assert false;
}



/**************************************************
 *                   DEFINITIONS                  *
 **************************************************/

definition excludeMethods(method f) returns bool =
    f.selector != depositBufferedEtherCall(uint256, bytes32, bytes32, uint256, uint256, bytes).selector
        && f.selector != _verifySignaturesCall(bytes32,uint256,bytes32,uint256,uint256,(bytes32,bytes32),(bytes32,bytes32)).selector;


definition onlyDeposit(method f) returns bool =
    f.selector == depositBufferedEther(uint256,bytes32,bytes32,uint256,uint256,bytes,(bytes32,bytes32)[]).selector;


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


// STATUS - verified
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

    require StkRouter.getStakingModuleStatus(_stakingModuleId) == 1;

    calldataarg args;
    f(e, args);

    assert StkRouter.getStakingModuleStatus(_stakingModuleId) == 0 
            => (getOwner() == e.msg.sender
                && f.selector == unpauseDeposits(uint256).selector);
}


// STATUS - verified
// If stakingModuleId was paused, owner can unpause
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
// It's impossible to stop deposits from DepositSecurityModule.sol
rule cantStop(env e, method f) filtered { f -> excludeMethods(f) } {
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
// guardians array can't contain the same guardian twice. guardians array and guardianIndicesOneBased mapping are correlated
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


// STATUS - verified
// Zero address can't be a guardian
invariant zeroIsNotGuardian()
    !isGuardian(0)
    filtered { f -> excludeMethods(f) }
    {
        preserved {
            require mirrorArrayLen < max_uint128;
            requireInvariant unique();  // need it to synchronize array and mapping
        }
    }


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


// STATUS - verified
// If canDeposit() returns false/reverts, depositBufferedEther() reverts
rule agreedRevertsSimple(env e, env e2, method f) filtered { f -> onlyDeposit(f) } {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;

    require e.block.number == e2.block.number;
    require e.msg.value == e2.msg.value && e.msg.value == 0;

    bool isDepositable = canDeposit@withrevert(e2, stakingModuleId);

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

    assert  (isCanDepositReverted || !isDepositable) => isDepositReverted;
}



/**************************************************
 *                   IN PROGRESS                  *
 **************************************************/


// only guardian can pause deposits
// STATUS - in progress: https://vaas-stg.certora.com/output/3106/7f9fb82c59374a3d8a8c0c31b98ec44c/?anonymousKey=e8037a9854892fd6131b4f61605eea484994cdd3
// There can be 2 issues:
// 1. struct is not passed correctly inside pauseDeposit()
rule onlyGuardianCanPause(env e, method f) filtered { f -> excludeMethods(f) } {
    uint256 blockNumber;
    uint256 stakingModuleId;
    DSM.Signature sig;

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
    
    uint256 before = getEthBalance(Lido);

    depositBufferedEtherCall(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    uint256 after = getEthBalance(Lido);

    depositBufferedEtherCall@withrevert(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    bool isReverted = lastReverted;

    assert (before - 32 == after) => isReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - in progress
// staking router balance remains the same
// Lido balance decreases by 32 ETH
// Lido deposit to StakingRouter didn't change ETH balances: https://vaas-stg.certora.com/output/3106/dbf11709d7b14512b8a6082dc8a97032/?anonymousKey=e9bcdd50b348d98cd84c87d62d48c1a18c24dbb6
// counter example shows that deposit wasn't reverted, but the call trace is not full
rule correct32EthDeposit(env e, method f) {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;
    
    uint256 lidoBalanceBefore = getEthBalance(Lido);
    uint256 stkRouterBalanceBefore = getEthBalance(StkRouter);

    depositBufferedEtherCall(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    uint256 lidoBalanceAfter = getEthBalance(Lido);
    uint256 stkRouterBalanceAfter = getEthBalance(StkRouter);

    // assert to_uint256(lidoBalanceBefore - 32) == lidoBalanceAfter => to_uint256(stkRouterBalanceBefore - 32) == stkRouterBalanceAfter, "Remember, with great power comes great responsibility.";
    // assert to_uint256(lidoBalanceBefore - 32) == lidoBalanceAfter;
    assert lidoBalanceBefore != lidoBalanceAfter;
    assert stkRouterBalanceBefore != stkRouterBalanceAfter, "Remember, with great power comes great responsibility.";
}



// STATUS - in progress
// checking depositBufferedEther 5/6 conditions from doc:
/**
     * Reverts if any of the following is true:
     *   1. IDepositContract.get_deposit_root() != depositRoot.
     *   2. StakingModule.getNonce() != nonce.
     *   3. The number of guardian signatures is less than getGuardianQuorum().
     *   4. An invalid or non-guardian signature received.   // check in another rule
     *   5. block.number - StakingModule.getLastDepositBlock() < minDepositBlockDistance.
     *   6. blockhash(blockNumber) != blockHash.
     */
rule revert5(env e, env e2, method f) {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;

    // bytes32 getDepositRootBefore = DepositContract.get_deposit_root(e);
    uint256 signaturesLengthBefore = getSortedGuardianSignaturesLength();
    uint256 nonceBefore = StkRouter.getStakingModuleNonce(e, stakingModuleId);
    uint256 quorumBefore = getGuardianQuorum();
    uint256 getStakingModuleLastDepositBlockBefore = StkRouter.getStakingModuleLastDepositBlock(e, stakingModuleId);
    uint256 minDepositBlockDistanceBefore = getMinDepositBlockDistance();
    bytes32 blockHashBefore = returnBlockHash(e, blockNumber);

    require e.block.number == e2.block.number;

    depositBufferedEtherCall@withrevert(e2,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    bool isReverted = lastReverted;

    assert // getDepositRootBefore != depositRoot   // deposit_contract is too heavy, need a workaround
                // || 
                nonceBefore != nonce
                || signaturesLengthBefore < quorumBefore
                || to_uint256(e2.block.number - getStakingModuleLastDepositBlockBefore) < minDepositBlockDistanceBefore
                || blockHashBefore != blockHash || blockHash == 0
            => isReverted, "Remember, with great power comes great responsibility.";
}

// STATUS - in progress / verified / error / timeout / etc.
// TODO: invariant description
invariant invariantName1(env e, uint256 blockNumber1, uint256 blockNumber2)
    blockNumber1 == blockNumber2 => returnBlockHash(e, blockNumber1) == returnBlockHash(e, blockNumber2)
    filtered { f -> simpleFunc(f) }

invariant invariantName2(env e, uint256 blockNumber1, uint256 blockNumber2)
    blockNumber1 == blockNumber2 => returnBlockHash(e, blockNumber1) != returnBlockHash(e, blockNumber2)
    filtered { f -> simpleFunc(f) }

definition simpleFunc(method f) returns bool =
    f.selector == setMinDepositBlockDistance(uint256).selector;

// STATUS - in progress
// After calling depositBufferedEther check that nonce was increased by 1
rule noncePlusOne(env e, method f) {
    uint256 blockNumber;
    bytes32 blockHash;
    bytes32 depositRoot;
    uint256 stakingModuleId;
    uint256 nonce;
    bytes depositCalldata;
    
    uint256 nonceBefore = StkRouter.getStakingModuleNonce(e, stakingModuleId);

    depositBufferedEtherCall(e,
        blockNumber,
        blockHash,
        depositRoot,
        stakingModuleId,
        nonce,
        depositCalldata
    );

    uint256 nonceAfter = StkRouter.getStakingModuleNonce(e, stakingModuleId);

    assert to_uint256(nonceBefore + 1) == nonceAfter, "Remember, with great power comes great responsibility.";
}