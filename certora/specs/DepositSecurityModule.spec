using LidoLocator as Locator
using DepositSecurityModuleHarness as DSM
using StakingRouter as StkRouter

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
}


definition excludeMethods(method f) returns bool =
    f.selector != depositBufferedEtherCall(uint256, bytes32, bytes32, uint256, uint256, bytes).selector;


rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}


//-----PROPERTIES-----
// uniqueness of guardianIndicesOneBased()
// STATUS - in progress (https://vaas-stg.certora.com/output/3106/3e9c46d0258d481ea256c5199219b266/?anonymousKey=8edf10f52fe75e0b85aa327ab469ec44dca32b0a )
invariant complexUniqueness(env e, address guardian1, address guardian2)
    ((guardianIndicesOneBased(guardian1) != 0 && guardianIndicesOneBased(guardian2) != 0)
        => (guardian1 != guardian2 
                <=> guardianIndicesOneBased(guardian1) != guardianIndicesOneBased(guardian2)))
    &&
    ((guardianIndicesOneBased(guardian1) != 0 && guardianIndicesOneBased(guardian2) == 0)
        => guardian1 != guardian2)
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
            requireInvariant indexLengthCheck(guardian1);
            requireInvariant indexLengthCheck(guardian2);
        }
    }

// STATUS - in progress (https://vaas-stg.certora.com/output/3106/3ac29048c01b4ed796abb2f6a5439925/?anonymousKey=76904c7e8f0901ce58e4b7e1f878d10d6c2f03ae)
invariant simpleUniqueness(env e, address guardian1, address guardian2)
    guardian1 != guardian2 <=> guardianIndicesOneBased(guardian1) != guardianIndicesOneBased(guardian2)
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
            requireInvariant indexLengthCheck(guardian1);
            requireInvariant indexLengthCheck(guardian2);
        }
    }


// https://vaas-stg.certora.com/output/3106/e55d99c0f86f440383ea6473ad684065/?anonymousKey=dea9f5835bb2d23c86d7b1dea3f03876ae3cc62f
invariant uniqueness(env e)
    (forall address guardian1. forall address guardian2. guardian1 != guardian2
        => (guardianIndicesOneBased(guardian1) != guardianIndicesOneBased(guardian2) 
            || guardianIndicesOneBased(guardian1) == 0)) 
    && 
    (forall int256 i. i < getGuardiansLength() 
        => to_mathint(guardianIndicesOneBased(getGuardian(to_uint256(i)))) == (to_uint256(i) + 1))
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
        }
    }


// correlation invariant for guardians and guardianIndicesOneBased: if a guardian, guardianIndicesOneBased should be > 0
// STATUS - in progress (https://vaas-stg.certora.com/output/3106/b7dfaf2e26be490bbc9c6abfc091a3a1/?anonymousKey=86d7cb8e44b732a0f701aac95b33a83bac2821c1)
// need uniqueness of guardianIndicesOneBased()
invariant correlation(env e, address guardian)
    guardianIndicesOneBased(guardian) > 0 
        <=> (getGuardian(guardianIndicesOneBased(guardian) - 1) == guardian && guardian != 0)
    filtered { f -> excludeMethods(f)  }
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
        }
    }
    


// STATUS - in progress (need correlation: https://vaas-stg.certora.com/output/3106/96f7160907bd4484b13ca890e6fa8b1a/?anonymousKey=13f35dc6c082604b4c5a760429e1407652e81b3e)
// guardianIndicesOneBased[addr] < guardians.length  (invariant from line 306)
invariant indexLengthCheck(address guardian)
    getGuardianIndex(guardian) < getGuardiansLength()
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
        }
    }


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


// if stakingModuleId is paused, can unpause:
//  - scenaro like: pauseDeposits() -> unpauseDeposits() doesn't revert (will need to eliminate many other revert scenarios)
//  - require that it's just paused -> unpauseDeposits() doesn't revert (will need to eliminate many other revert scenarios)

// only guardian can pause deposits

// Hristo said that they are worried about DoS and integrity becuase there are many modules in their system, but do we have any good properties to check? most of them seems very straightforward, like below
// cooperation between DepositSecurityModule and StakingRouter :
// - if stakingModuleId is paused 
//      - canDeposit() returns false
//      - depositBufferedEther() reverts
// affect of deposit on Lido.sol - need it?




// can't deposit with the same input twice
// STATUS - violated - possible deposit twice. is it intended? 
// (maybe it's violated becuase of unresolved call: https://vaas-stg.certora.com/output/3106/333fc9f51bf749c4ab27d7d23ebb5dec/?anonymousKey=176deebf3170bcb66cdf1ebe90e089581609fec7. Looks like the issue with a dispatcher becuase deposit() was summarized)
rule cannotdepositTwice(env e, method f) {
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


//-----IDEAS-----
// checking signatures (Merkle tree (kind of)) in _verifySignatures(). do we have an example?



