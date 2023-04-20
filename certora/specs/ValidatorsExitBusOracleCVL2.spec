 using ValidatorsExitBusOracleHarness as VEBO;
using OracleReportSanityChecker as SanityCheck;

methods {
    // IConsensusContract = MockConsensusContract.sol
    function _.getChainConfig() external => DISPATCHER(true);
    function _.getInitialRefSlot() external => DISPATCHER(true);
    function _.getIsMember(address) external => DISPATCHER(true);
    function _.getCurrentFrame() external => DISPATCHER(true);

    // Locator = LidoLocator.sol
    function _.stakingRouter() external => NONDET;
    function _.oracleReportSanityChecker() external => NONDET;
    function _.withdrawalQueue() external => NONDET;

    // OracleReportSanityChecker = OracleReportSanityChecker.sol
    function _.checkExitBusOracleReport(uint256) external => DISPATCHER(true);
    // checkNodeOperatorsPerExtraDataItemCount(uint256, uint256) => DISPATCHER(true)
    // checkAccountingExtraDataListItemsCount(uint256) => DISPATCHER(true)
    // checkExitedValidatorsRatePerDay(uint256) => DISPATCHER(true)
    function _.getOracleReportLimits() external => DISPATCHER(true);

    function getConsensusReport() external returns(bytes32, uint256, uint256, bool) envfree;

    function hasRole(bytes32, address) external returns(bool) envfree;
    function DEFAULT_ADMIN_ROLE() external returns(bytes32) envfree;
    function getResumeSinceTimestamp() external returns(uint256) envfree;
    function RESUME_ROLE() external returns(bytes32) envfree;
    function SUBMIT_DATA_ROLE() external returns(bytes32) envfree;
    function getTotalRequestsProcessed() external returns(uint256) envfree;
    function getMaxValidatorExitRequestsPerReport() external returns(uint256) envfree;
    function getLastProcessingRefSlot() external returns(uint256) envfree;

    function compareBytes(bytes, bytes) external returns(bool) envfree;

    // function dataGlobal() external returns(ValidatorsExitBusOracleHarness.ReportData) envfree;
    // function checkGlobal() external returns(uint256) envfree;

    function getConsensusVersionGlobal() external returns(uint256) envfree;
    function getRefSlotGlobal() external returns(uint256) envfree;
    function getRequestsCountGlobal() external returns(uint256) envfree;
    function getDataFormatGlobal() external returns(uint256) envfree;
    function getDataGlobal() external returns(bytes) envfree;
    function matchReportDatas(uint256, uint256, uint256, uint256, bytes) external returns(bool) envfree;
}

definition excludeInitialize(method f) returns bool =
    f.selector != sig:initialize(address, address, uint256, uint256).selector;

// definition excludeHelper(method f) returns bool =
//     f.selector != sig:submitReportDataHelper(uint256, uint256, uint256, uint256, bytes, uint256).selector;


definition matchReportDataWithGlobal(uint256 consensusVersion, uint256 refSlot, uint256 requestsCount, uint256 dataFormat) returns bool = 
    consensusVersion == getConsensusVersionGlobal()
    && refSlot == getRefSlotGlobal()
    && requestsCount == getRequestsCountGlobal()
    && dataFormat == getDataFormatGlobal()
    // && compareBytes(dataInput, dataGlobal)
    ;


rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}

rule sanitySubmit(env e1, env e2) {
    calldataarg args1;
    calldataarg args2;
    submitReportData(e1, args1);
    submitReportData(e2, args2);
    assert false;
}


// STATUS - in progress (can be violated becuase admin can set new admin to 0 in grantRole(bytes32,address))
// admin != 0
invariant adminIsNotZero(address admin)
    hasRole(DEFAULT_ADMIN_ROLE(), admin) => admin != 0


// STATUS - verified
// can't initialize twice
rule cantInitializeTwice(env e, env e2, method f, method g) 
    filtered { f -> f.selector == sig:initialize(address, address, uint256, uint256).selector,
               g -> g.selector == sig:initialize(address, address, uint256, uint256).selector } {

    calldataarg args;
    calldataarg args2;

    f(e, args);
    g@withrevert(e2, args2);

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


// STATUS - in progress 
// report only processed once / can't submit twice
// rule cantSubmitReportTwice(env e, env e2, method f, method g) {
//     uint256 contractVersion1;    uint256 contractVersion2;
//     uint256 consensusVersion1;   uint256 consensusVersion2;
//     uint256 refSlot1;            uint256 refSlot2;
//     uint256 requestsCount1;      uint256 requestsCount2;
//     uint256 dataFormat1;         uint256 dataFormat2;
//     bytes   dataInput1;          bytes   dataInput2;

//     // bytes dataGlobalVar = getDataGlobal();

//     calldataarg args1;
//     calldataarg args2;

//     // require matchReportDataWithGlobal(consensusVersion1, refSlot1, requestsCount1, dataFormat1);
//     submitReportData1(e, args1);
    
//     // require matchReportDataWithGlobal(consensusVersion2, refSlot2, requestsCount2, dataFormat2);
//     submitReportData2(e2, args2);
//     // bool isReverted = lastReverted;

//     // assert (e.block.timestamp == e2.block.timestamp 
//     //             || (contractVersion1 == contractVersion2 
//     //                 && consensusVersion1 == consensusVersion2 
//     //                 && refSlot1 == refSlot2 
//     //                 && requestsCount1 == requestsCount2 
//     //                 && dataFormat1 == dataFormat2 
//     //                 // && compareBytes(dataInput1, dataInput2)
//     //                 ))            
//     //         => isReverted, "Remember, with great power comes great responsibility.";
//     assert false;
// }


// STATUS - verified
// getTotalRequestsProcessed can't be decreased
rule totalRequestsProcessedMonotonicity(env e, method f) {

    uint256 requestsBefore = getTotalRequestsProcessed();

    calldataarg args;
    f(e, args);

    uint256 requestsAfter = getTotalRequestsProcessed();

    assert requestsBefore <= requestsAfter, "Remember, with great power comes great responsibility.";
}


// STATUS - verified
// !dataSubmitted && e.block.timestamp > processingDeadlineTime => report can't be submitted
rule cannotSubmitAnymore(env e, env e2) {
    uint256 currentFrameRefSlotBefore;      uint256 currentFrameRefSlotAfter;
    uint256 processingDeadlineTimeBefore;   uint256 processingDeadlineTimeAfter;
    bytes32 dataHashBefore;                 bytes32 dataHashAfter;
    bool    dataSubmittedBefore;            bool    dataSubmittedAfter;
    uint256 dataFormatProcessingBefore;     uint256 dataFormatProcessingAfter;
    uint256 requestsCountProcessingBefore;  uint256 requestsCountProcessingAfter;
    uint256 requestsSubmittedBefore;        uint256 requestsSubmittedAfter;

    uint256 contractVersion;
    uint256 consensusVersion;
    uint256 refSlot;
    uint256 requestsCount;
    uint256 dataFormat;
    bytes dataInput;

    require consensusVersion == getConsensusVersionGlobal();
    require refSlot == getRefSlotGlobal();
    require requestsCount == getRequestsCountGlobal();
    require dataFormat == getDataFormatGlobal();

    currentFrameRefSlotBefore, 
        processingDeadlineTimeBefore, 
        dataHashBefore,
        dataSubmittedBefore,
        dataFormatProcessingBefore,
        requestsCountProcessingBefore,
        requestsSubmittedBefore = getProcessingState(e);

    // submitReportDataHelper@withrevert(e, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);
    ValidatorsExitBusOracleHarness.ReportData data;
    submitReportData(e, data, contractVersion);

    currentFrameRefSlotAfter, 
        processingDeadlineTimeAfter, 
        dataHashAfter,
        dataSubmittedAfter,
        dataFormatProcessingAfter,
        requestsCountProcessingAfter,
        requestsSubmittedAfter = getProcessingState(e);

    assert !dataSubmittedBefore && e.block.timestamp > processingDeadlineTimeBefore => !dataSubmittedAfter, "Remember, with great power comes great responsibility.";
}

// STATUS - verified (3/3 assertions)
// can't exit more validators than a limit
// missed a deadline, can't submit a report
// if requestsCount was 0, TOTAL_REQUESTS_PROCESSED_POSITION remains unchanged
rule submitReportDataIntegrity(env e, env e2) {
    uint256 contractVersion;
    bytes32 hash;
    uint256 refSlotReport;
    uint256 deadline;
    bool processingStarted;
    uint256 max = getMaxValidatorExitRequestsPerReport();

    uint256 consensusVersion;
    uint256 refSlot;
    uint256 requestsCount;
    uint256 dataFormat;
    bytes dataInput;

    uint256 totalRequestsProcessedBefore = getTotalRequestsProcessed();

    require matchReportDataWithGlobal(consensusVersion, refSlot, requestsCount, dataFormat, dataInput);
    require (hash, refSlotReport, deadline, processingStarted) == getConsensusReport();

    submitReportDataHelper@withrevert(e, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);
    bool isReverted = lastReverted;

    uint256 totalRequestsProcessedAfter = getTotalRequestsProcessed();

    assert e.block.timestamp > deadline => lastReverted;
    assert requestsCount > max => lastReverted;
    assert requestsCount == 0 => totalRequestsProcessedBefore == totalRequestsProcessedAfter;
    // assert false;
}


rule refTiemIncreases(env e, env e2) {
    uint256 currentFrameRefSlotBefore;      uint256 currentFrameRefSlotAfter;
    uint256 processingDeadlineTimeBefore;   uint256 processingDeadlineTimeAfter;
    bytes32 dataHashBefore;                § bytes32 dataHashAfter;
    bool    dataSubmittedBefore;            bool    dataSubmittedAfter;
    uint256 dataFormatProcessingBefore;     uint256 dataFormatProcessingAfter;
    uint256 requestsCountProcessingBefore;  uint256 requestsCountProcessingAfter;
    uint256 requestsSubmittedBefore;        uint256 requestsSubmittedAfter;
    
    currentFrameRefSlotBefore, 
        processingDeadlineTimeBefore, 
        dataHashBefore,
        dataSubmittedBefore,
        dataFormatProcessingBefore,
        requestsCountProcessingBefore,
        requestsSubmittedBefore = getProcessingState(e);

    // submitReportDataHelper@withrevert(e, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);

    currentFrameRefSlotAfter, 
        processingDeadlineTimeAfter, 
        dataHashAfter,
        dataSubmittedAfter,
        dataFormatProcessingAfter,
        requestsCountProcessingAfter,
        requestsSubmittedAfter = getProcessingState(e2);

    assert e.block.timestamp < e2.block.timestamp => currentFrameRefSlotBefore < currentFrameRefSlotAfter;
}


// STATUS - in progress
// no function, except submitReportData(), can change the value in LAST_PROCESSING_REF_SLOT_POSITION
// After successfully processing a consensus report, the LastProcessingRefSlot is updated correctly
rule whoCanChangeLastProcessingEtc(env e, method f) filtered { f -> excludeInitialize(f) && excludeHelper(f) } {

    uint256 getLastProcessingRefSlotBefore = getLastProcessingRefSlot();

    calldataarg args;
    f(e, args);

    uint256 getLastProcessingRefSlotAfter = getLastProcessingRefSlot();

    assert getLastProcessingRefSlotBefore != getLastProcessingRefSlotAfter
            => f.selector == submitReportData1((uint256,uint256,uint256,uint256,bytes),uint256).selector;
}



//------IDEAS-----//

// last report processing time is always increasing
// can't submit a report that is before the last processing time
// each report should have a deadline

// From Hristo's spec:
// Only newer report, pointing to higher refSlot, can be submitted



// getLastRequestedValidatorIndices()

// there can't be the same index
// index shouldn't decrease (Node Op Validator Index Must Increase (...BusOracle.sol -> _processExitRequestsList() -> NodeOpValidatorIndexMustIncrease()))





// getProcessingState()

// requestsSubmitted <= requestsCount

// !dataSubmitted && e.block.timestamp > processingDeadlineTime => it can never be submitted


// @notice Hash of the report data. Zero bytes if consensus on the hash hasn't
// been reached yet for the current reporting frame.
// bytes32 dataHash;
// any way to check it? 

// if ref slot was changed, get processing state doesn't mix up

// refSlotBefore != refSlotAfter => hashAfter == 0
// hashBefore == 0 && hashAfter => e.msg.sender == CONSENSUS_CONTRACT_POSITION.getStorageAddress()
