using ValidatorsExitBusOracleHarness as VEBO
using OracleReportSanityChecker as SanityCheck

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
    getOracleReportLimits() returns(uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256) => DISPATCHER(true)


    getConsensusReport() returns(bytes32, uint256, uint256, bool) envfree


    hasRole(bytes32, address) returns(bool) envfree
    DEFAULT_ADMIN_ROLE() returns(bytes32) envfree
    getResumeSinceTimestamp() returns(uint256) envfree
    RESUME_ROLE() returns(bytes32) envfree
    getTotalRequestsProcessed() returns(uint256) envfree
    getMaxValidatorExitRequestsPerReport() returns(uint256) envfree
}

definition excludeInitialize(method f) returns bool =
    f.selector != initialize(address, address, uint256, uint256).selector;


rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}


// STATUS - in progress (can be violated becuase admin can set new admin to 0 in grantRole(bytes32,address))
// admin != 0
invariant adminIsNotZero(address admin)
    hasRole(DEFAULT_ADMIN_ROLE(), admin) => admin != 0


// STATUS - verified
// can't initialize twice
rule cantInitializeTwice(env e) {
    address admin;
    address consensusContract;
    uint256 consensusVersion;
    uint256 lastProcessingRefSlot;

    initialize(e, admin, consensusContract, consensusVersion, lastProcessingRefSlot);

    initialize@withrevert(e, admin, consensusContract, consensusVersion, lastProcessingRefSlot);

    assert lastReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// Only a user with necessary role can resume within pause timeframe
rule canResume(env e, env e2) {
    bool pausedBefore = isPaused(e);

    require e.msg.sender == e2.msg.sender;

    resume@withrevert(e2);
    bool isReverted = lastReverted;

    bool pausedAfter = isPaused(e2);

    assert (e2.msg.value == 0 
                && pausedBefore 
                && e2.block.timestamp < getResumeSinceTimestamp()
                && hasRole(RESUME_ROLE(), e2.msg.sender))
            => (!isReverted 
                && !pausedAfter);
}


// STATUS - verified
// report only processed once / can't submit twice
rule cantSubmitReportTwice(env e, method f) {
    VEBO.ReportData data; 
    uint256 contractVersion;

    submitReportData(e, data, contractVersion);

    submitReportData@withrevert(e, data, contractVersion);

    assert lastReverted, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// getTotalRequestsProcessed can't be decreased
rule totalRequestsProcessedMonotonicity(env e, method f) {

    uint256 requestsBefore = getTotalRequestsProcessed();

    calldataarg args;
    f(e, args);

    uint256 requestsAfter = getTotalRequestsProcessed();

    assert requestsBefore <= requestsAfter, "Remember, with great power comes great responsibility.";
}


// STATUS - in progress
// only one report per slot can be processed (Need help to understand where it's stated in the code)
rule needMoreSlots(env e, method f) {
    VEBO.ReportData data1;      VEBO.ReportData data2; 
    uint256 contractVersion1;   uint256 contractVersion2;

    submitReportData(e, data1, contractVersion2);

    submitReportData@withrevert(e, data1, contractVersion2);
    bool isReverted = lastReverted;

    assert isReverted => data1.refSlot == data2.refSlot, "Remember, with great power comes great responsibility.";
}


// can't exit more validators than a limit
// missed a deadline, can't submit a report
// requestsCount can't be 0
rule submitReportDataIntegrity(env e) {
    VEBO.ReportData data;  
    uint256 consensusVersion;
    uint256 refSlot;
    uint256 requestsCount;
    uint256 dataFormat;
    bytes dataInput;
    uint256 contractVersion;

    bytes32 hash;
    uint256 refSlotReport;
    uint256 deadline;
    bool processingStarted;
    uint256 max = getMaxValidatorExitRequestsPerReport();

    require data.consensusVersion == consensusVersion;
    require data.refSlot == refSlot;
    require data.requestsCount == requestsCount;
    require data.dataFormat == dataFormat;
    // require data.data == dataInput;
    require compareBytes(e, data.data, dataInput);

    require (hash, refSlotReport, deadline, processingStarted) == getConsensusReport();

    // submitReportData@withrevert(e, data, contractVersion);
    submitReportDataHelper@withrevert(e, data, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);
    bool isReverted = lastReverted;

    assert (e.block.timestamp > deadline || data.requestsCount > max) => lastReverted;
}


//------IDEAS-----//

// last report processing time is always increasing
// can't submit a report that is before the last processing time
// each report should have a deadline


// can getLastRequestedValidatorIndices return the same indices for different moduleIds or nodeOpIds?
// Node Op Validator Index Must Increase (...BusOracle.sol - line 168)
// there can't be the same index

// validator can request exit only by been included in submitReportData()



// getProcessingState()
// requestsSubmitted <= requestsCount
// !dataSubmitted && e.block.timestamp > processingDeadlineTime => it can never be submitted

// if I call getProcessingState(), then it will be processed in submit? When/how getProcessingState() is supposed to be called?
// if report was submitted, data should be submitted as well
