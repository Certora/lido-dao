methods {
    // IConsensusContract = MockConsensusContract.sol
    getChainConfig() returns(uint256, uint256, uint256) => DISPATCHER(true)
    getInitialRefSlot() returns(uint256) => DISPATCHER(true)
    getIsMember(address) returns(bool) => DISPATCHER(true)
    getCurrentFrame() returns(uint256, uint256) => DISPATCHER(true)

    // Locator = LidoLocator.sol
    stakingRouter() returns(address) => NONDET
    oracleReportSanityChecker() returns(address) => NONDET
    withdrawalQueue() returns(address) => NONDET

    // OracleReportSanityChecker = OracleReportSanityChecker.sol
    checkExitBusOracleReport(uint256) => DISPATCHER(true)
    // checkNodeOperatorsPerExtraDataItemCount(uint256, uint256) => DISPATCHER(true)
    // checkAccountingExtraDataListItemsCount(uint256) => DISPATCHER(true)
    // checkExitedValidatorsRatePerDay(uint256) => DISPATCHER(true)
}


// need to understand syste more to resolve calls, however, they are just NONDET, so no need to resolve them until they cause false violations 
// https://vaas-stg.certora.com/output/3106/3ad7d13c5d9f4196b9404ded723b9574/?anonymousKey=2c3653b2ce52320bbc0d21755f08d78796a5f69c
rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}




//------IDEAS-----//
// can unpause
// can't unpuse before time reached
// only a user with specific role can unpause
// admin != 0