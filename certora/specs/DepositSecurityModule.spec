using LidoLocator as Locator
using DepositSecurityModuleHarness as DSM

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
        get_deposit_root() returns(bytes32) => DISPATCHER(true)

    // StakingModuleMock.sol
    // havoc - "only the return value"
        getStakingModuleSummary() returns(uint256, uint256, uint256) => DISPATCHER(true)
        getNonce() returns (uint256) => DISPATCHER(true)


    // DepositSecurityModule.sol
    guardianIndicesOneBased(address) returns(uint256) envfree
    getGuardian(uint256) returns(address) envfree
    getGuardianIndex(address) returns(int256) envfree
    getGuardiansLength() returns(int256) envfree
}

rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}



//-----PROPERTIES-----
// correlation invariant for guardians and guardianIndicesOneBased: if a guardian, guardianIndicesOneBased should be > 0
// STATUS - in progress (https://vaas-stg.certora.com/output/3106/b7dfaf2e26be490bbc9c6abfc091a3a1/?anonymousKey=86d7cb8e44b732a0f701aac95b33a83bac2821c1)
invariant correlation(env e, address guardian)
    guardianIndicesOneBased(guardian) > 0 <=> getGuardian(guardianIndicesOneBased(guardian) - 1) == guardian
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
        }
    }


// STATUS - in progress (need correlation: https://vaas-stg.certora.com/output/3106/96f7160907bd4484b13ca890e6fa8b1a/?anonymousKey=13f35dc6c082604b4c5a760429e1407652e81b3e)
// guardianIndicesOneBased[addr] < guardians.length  (invariant from line 306)
invariant indexLengthCheck(env e, address guardian)
    getGuardianIndex(guardian) < getGuardiansLength()
    {
        preserved {
            require getGuardiansLength() >= 0 && getGuardiansLength() <= 100000000;
        }
    }


// onlyOwner can change owner, pauseIntentValidityPeriodBlocks, maxDepositsPerBlock, minDepositBlockDistance, quorum; add/remove guardians, unpause deposits

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

//-----IDEAS-----
// checking signatures (Merkle tree (kind of)) in _verifySignatures(). do we have an example?



// can deposit with the same stakingModuleId twice?
// STATUS - violated - possible deposit twice. is it intended? 
// TODO: rule description
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