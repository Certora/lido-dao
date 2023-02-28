/**************************************************
 *                 Methods Declaration            *
 **************************************************/
methods {
    // IConsensusContract = MockConsensusContract.sol
    getChainConfig() returns (uint256, uint256, uint256) => DISPATCHER(true)
    getCurrentFrame() returns (uint256, uint256) => DISPATCHER(true)
    getIsMember(address) returns (bool) => DISPATCHER(true)
    getFrameConfig() returns (uint256, uint256) => DISPATCHER(true)

    // Locator = LidoLocator.sol
    stakingRouter() returns(address) => NONDET
    oracleReportSanityChecker() returns(address) => NONDET
    withdrawalQueue() returns(address) => NONDET

    // StakingRouter = StakingRouter.sol
    reportStakingModuleExitedValidatorsCountByNodeOperator(uint256, bytes, bytes) => DISPATCHER(true)
    reportStakingModuleStuckValidatorsCountByNodeOperator(uint256, bytes, bytes) => DISPATCHER(true)
    onValidatorsCountsByNodeOperatorReportingFinished() => DISPATCHER(true)
    getExitedValidatorsCountAcrossAllModules() returns (uint256) => DISPATCHER(true)
    updateExitedValidatorsCountByStakingModule(uint256[], uint256[]) => DISPATCHER(true)

    // OracleReportSanityChecker = OracleReportSanityChecker.sol
    checkNodeOperatorsPerExtraDataItemCount(uint256, uint256) => DISPATCHER(true)
    checkAccountingExtraDataListItemsCount(uint256) => DISPATCHER(true)
    checkExitedValidatorsRatePerDay(uint256) => DISPATCHER(true)

    // LegacyOracle = MockLegacyOracle.sol
    getBeaconSpec() returns (uint64, uint64, uint64, uint64) => DISPATCHER(true) // might be able to simplify, only used for one check
    getLastCompletedEpochId() returns (uint256) => DISPATCHER(true)
    handleConsensusLayerReport(uint256, uint256, uint256) => DISPATCHER(true)
    getConsensusContract() returns (address) => NONDET //DISPATCHER(true)
    getAccountingOracle() returns (address) => NONDET //getAccountingOracleContract()

    // WithdrawalQueue = WithdrawalQueue.sol
    updateBunkerMode(bool, uint256) => DISPATCHER(true)

    // Lido = MockLidoForAccountingOracle.sol
    handleOracleReport(uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)

    // StakingModule = StakingModuleMock.sol
    getStakingModuleSummary() returns (uint256, uint256, uint256) => DISPATCHER(true)
    onExitedAndStuckValidatorsCountsUpdated() => DISPATCHER(true)
    updateExitedValidatorsCount(bytes, bytes) => DISPATCHER(true)
    updateStuckValidatorsCount(bytes, bytes) => DISPATCHER(true)
}

/**************************************************
 *               CVL FUNCS & DEFS                 *
 **************************************************/
function getAccountingOracleContract() returns address {
    return currentContract;
}

// rule ideas:
//  1. verify all the reverting scenarios of submitReportData()
//  2. verify submitReportData() does not revert outside of the allowed reverting scenarios
//  3. verify all the errors on lines 91-110 are caught correctly
//  4. 



/**************************************************
 *                 MISC Rules                     *
 **************************************************/
rule sanity(method f) 
{
    env e;
    calldataarg args;
    f(e,args);
    assert false;
}

rule shouldNotRevert(method f)
filtered{f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector}
{
    env e;
    calldataarg args;
    f@withrevert(e,args);
    assert (!lastReverted);
}