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

    // AccessControl.sol
    hasRole(bytes32, address) returns(bool) => DISPATCHER(true)
    SUBMIT_DATA_ROLE() returns(bytes32) => DISPATCHER(true)

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
    SUBMIT_DATA_ROLE() returns(bytes32) envfree
    getTotalRequestsProcessed() returns(uint256) envfree
    getMaxValidatorExitRequestsPerReport() returns(uint256) envfree
    getLastProcessingRefSlot() returns(uint256) envfree
    getConsensusVersion() returns(uint256) envfree

    compareBytes(bytes, bytes) returns(bool) envfree

    dataGlobal() returns(uint256, uint256, uint256, uint256, bytes) envfree
    checkGlobal() returns(uint256) envfree

    getConsensusVersionGlobal() returns(uint256) envfree
    getRefSlotGlobal() returns(uint256) envfree
    getRequestsCountGlobal() returns(uint256) envfree
    getDataFormatGlobal() returns(uint256) envfree
    getDataGlobal() returns(bytes) envfree
    matchReportDatas(uint256, uint256, uint256, uint256, bytes) returns(bool) envfree
    isConsensusMember(address) returns(bool) envfree
    checkContractVersion(uint256) envfree
    getRefSlot() returns(uint256) envfree
    getReportHash() returns(bytes32) envfree
    hashData() returns(bytes32) envfree
}

definition excludeInitialize(method f) returns bool =
    f.selector != initialize(address, address, uint256, uint256).selector;

definition excludeHelper(method f) returns bool =
    f.selector != submitReportDataHelper(uint256, uint256, uint256, uint256, bytes, uint256).selector;


definition matchReportDataWithGlobal(uint256 consensusVersion, uint256 refSlot, uint256 requestsCount, uint256 dataFormat) returns bool = 
    consensusVersion == getConsensusVersionGlobal()
    && refSlot == getRefSlotGlobal()
    && requestsCount == getRequestsCountGlobal()
    && dataFormat == getDataFormatGlobal()
    // && compareBytes(dataInput, dataGlobal)
    ;


// STATUS - in progress (can be violated becuase admin can remove it's own role)
// admin != 0
invariant adminIsNotZero(address admin)
    hasRole(DEFAULT_ADMIN_ROLE(), admin) => admin != 0


// STATUS - verified
//  It must not be possible to initialize twice.
rule cantInitializeTwice(env e, env e2, method f, method g) 
    filtered { f -> f.selector == initialize(address, address, uint256, uint256).selector,
               g -> g.selector == initialize(address, address, uint256, uint256).selector } {

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


// STATUS - verified
// It must not be possible to submit the same report twice. 
rule cantSubmitReportTwice(env e, env e2, method f, method g) {
    uint256 contractVersion1;    uint256 contractVersion2;
    uint256 consensusVersion1;   uint256 consensusVersion2;
    uint256 refSlot1;            uint256 refSlot2;
    uint256 requestsCount1;      uint256 requestsCount2;
    uint256 dataFormat1;         uint256 dataFormat2;
    bytes   dataInput1;          bytes   dataInput2;

    require matchReportDatas(consensusVersion1, refSlot1, requestsCount1, dataFormat1, dataInput1);
    submitReportDataHelper(e, consensusVersion1, refSlot1, requestsCount1, dataFormat1, dataInput1, contractVersion1);
    
    require matchReportDatas(consensusVersion2, refSlot2, requestsCount2, dataFormat2, dataInput2);
    submitReportDataHelper@withrevert(e2, consensusVersion2, refSlot2, requestsCount2, dataFormat2, dataInput2, contractVersion2);
    bool isReverted = lastReverted;

    assert (e.block.timestamp == e2.block.timestamp 
                || (contractVersion1 == contractVersion2 
                    && consensusVersion1 == consensusVersion2 
                    && refSlot1 == refSlot2 
                    && requestsCount1 == requestsCount2 
                    && dataFormat1 == dataFormat2 
                    ))            
            => isReverted, "Remember, with great power comes great responsibility.";
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


// STATUS - verified
// if repor data wasn't submitted and deadline (ConsensusReport.processingDeadlineTime) is passed, then data can't be submitted
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

    submitReportDataHelper@withrevert(e, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);

    currentFrameRefSlotAfter, 
        processingDeadlineTimeAfter, 
        dataHashAfter,
        dataSubmittedAfter,
        dataFormatProcessingAfter,
        requestsCountProcessingAfter,
        requestsSubmittedAfter = getProcessingState(e);

    assert !dataSubmittedBefore && e.block.timestamp > processingDeadlineTimeBefore => !dataSubmittedAfter, "Remember, with great power comes great responsibility.";
}

// STATUS - verified (7/7 assertions)
// can't exit more validators than a limit
// if requestsCount was 0, TOTAL_REQUESTS_PROCESSED_POSITION remains unchanged
// - The caller is not a member of the oracle committee and doesn't possess the SUBMIT_DATA_ROLE.
// - The provided contract version is different from the current one.
// - The provided consensus version is different from the expected one.
// - The provided reference slot differs from the current consensus frame's one.
// - The processing deadline for the current consensus frame is missed.
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

    bool isAllowed;
    require isAllowed == (hasRole(SUBMIT_DATA_ROLE(), e.msg.sender) 
                            || isConsensusMember(e.msg.sender));

    checkContractVersion@withrevert(contractVersion);
    bool contracrVersionReverted = lastReverted;

    uint256 consensusVersionBefore = getConsensusVersion(); 

    uint256 refSlotBefore = getRefSlot();

    bytes32 reportHashBefore = getReportHash();

    submitReportDataHelper@withrevert(e, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);
    bool isReverted = lastReverted;

    uint256 totalRequestsProcessedAfter = getTotalRequestsProcessed();

    assert requestsCount > max => isReverted;
    assert requestsCount == 0 => totalRequestsProcessedBefore == totalRequestsProcessedAfter;
    assert !isAllowed => isReverted;    // The caller is not a member of the oracle committee and doesn't possess the SUBMIT_DATA_ROLE.
    assert contracrVersionReverted => isReverted;   // The provided contract version is different from the current one.
    assert consensusVersionBefore != consensusVersion => isReverted;   // The provided consensus version is different from the expected one.
    assert refSlotBefore != refSlot => isReverted;   // The provided reference slot is different from the expected one.
    assert e.block.timestamp > deadline => isReverted; // The processing deadline for the current consensus frame is missed.
}


// STATUS - verified
// no function, except submitReportData(), can change the value in LAST_PROCESSING_REF_SLOT_POSITION
rule whoCanChangeLastProcessingEtc(env e, method f) filtered { f -> excludeInitialize(f) && excludeHelper(f) } {

    uint256 getLastProcessingRefSlotBefore = getLastProcessingRefSlot();

    calldataarg args;
    f(e, args);

    uint256 getLastProcessingRefSlotAfter = getLastProcessingRefSlot();

    assert getLastProcessingRefSlotBefore != getLastProcessingRefSlotAfter
            => f.selector == submitReportData((uint256,uint256,uint256,uint256,bytes),uint256).selector;
}


// STATUS - verified
// After successfully processing a consensus report, the lastProcessingRefSlot must be updated correctly
rule correctUpdateOfLastProcessingRefSlot() {
    env e; env e2; env e3;

    uint256 lastProcessingRefSlotBefore = getLastProcessingRefSlot();

    uint256 contractVersion;
    uint256 consensusVersion;   
    uint256 refSlot;            
    uint256 requestsCount;      
    uint256 dataFormat;         
    bytes   dataInput;          

    require matchReportDatas(consensusVersion, refSlot, requestsCount, dataFormat, dataInput);
    submitReportDataHelper(e, consensusVersion, refSlot, requestsCount, dataFormat, dataInput, contractVersion);

    uint256 lastProcessingRefSlotAfter = getLastProcessingRefSlot();

    assert lastProcessingRefSlotAfter == refSlot;
}


// STATUS - verified
// getLastRequestedValidatorIndices() can't return the same index for the same nodeOpId for the same nodeOpIds
rule noSameIndex(env e, method f) {
    uint256 moduleId; 
    uint256[] nodeOpIds;
    
    int256 indicesBefore1;
    int256 indicesBefore2;
    int256 indicesBefore3;

    int256 indicesAfter1;
    int256 indicesAfter2;
    int256 indicesAfter3;

    indicesBefore1, indicesBefore2, indicesBefore3 = callGetLastRequestedValidatorIndices(e, moduleId, nodeOpIds);

    calldataarg args;
    f(e, args);

    indicesAfter1, indicesAfter2, indicesAfter3 = callGetLastRequestedValidatorIndices(e, moduleId, nodeOpIds);

    assert (indicesBefore1 != indicesBefore2 
                && indicesBefore2 != indicesBefore3 
                && indicesBefore1 != indicesBefore3)
            => ((indicesAfter1 != indicesAfter2 
                    && indicesAfter2 != indicesAfter3 
                    && indicesAfter1 != indicesAfter3)
                && (indicesBefore1 == indicesAfter1
                    && indicesBefore2 == indicesAfter2
                    && indicesBefore3 == indicesAfter3));
}

// STATUS - verified
// index from getLastRequestedValidatorIndices() shouldn't decrease
rule indexIncrease(env e, method f) {
    uint256 moduleId; 
    uint256[] nodeOpIds;
    
    int256 indicesBefore1;
    int256 indicesBefore2;
    int256 indicesBefore3;

    int256 indicesAfter1;
    int256 indicesAfter2;
    int256 indicesAfter3;

    indicesBefore1, indicesBefore2, indicesBefore3 = callGetLastRequestedValidatorIndices(e, moduleId, nodeOpIds);

    calldataarg args;
    f(e, args);

    indicesAfter1, indicesAfter2, indicesAfter3 = callGetLastRequestedValidatorIndices(e, moduleId, nodeOpIds);

    assert (indicesBefore1 <= indicesBefore2 
                && indicesBefore2 <= indicesBefore3)
            => (indicesAfter1 <= indicesAfter2 
                    && indicesAfter2 <= indicesAfter3);
}