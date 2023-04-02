// using AccountingOracle as AccountingOracleContract


/**************************************************
 *               Methods Declaration              *
 **************************************************/
methods {
    submitConsensusReport(bytes32 report, uint256 refSlot, uint256 deadline) => NONDET
    getLastProcessingRefSlot() returns (uint256) => NONDET
    getConsensusVersion() returns (uint256) => NONDET
}

/**************************************************
 *                CVL FUNCS & DEFS                *
 **************************************************/
function saneTimeConfig() {
    env e0; calldataarg args0;

    require e0.msg.value == 0;                       // view functions revert is you send eth
    require e0.block.timestamp > 1672531200;         // 01.01.2023 00:00:00
    require e0.block.timestamp < 2524608000;         // 01.01.2050 00:00:00

    uint256 slotsPerEpoch; uint256 secondsPerSlot; uint256 genesisTime;
    slotsPerEpoch, secondsPerSlot, genesisTime = getChainConfig(e0);

    require slotsPerEpoch == 32;                    // simplification, must be required at constructor
    require secondsPerSlot == 12;                   // simplification, must be required at constructor
    require genesisTime < e0.block.timestamp;       // safe assumption, must be required at constructor

    uint256 initialEpoch; uint256 epochsPerFrame; uint256 fastLaneLengthSlots;
    initialEpoch, epochsPerFrame, fastLaneLengthSlots = getFrameConfig(e0);
    require epochsPerFrame > 0;                     // constructor already ensures this
    require epochsPerFrame < 31536000;              // assuming less than 1 year per frame

    // assuming correct configuration of the frame, otherwise revert
    require initialEpoch < (e0.block.timestamp - genesisTime) / (secondsPerSlot * slotsPerEpoch);
    require initialEpoch > 0;    
}

definition UINT64_MAX() returns uint64 = 0xFFFFFFFFFFFFFFFF;
definition UINT256_MAX() returns uint256 = 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff;

// definition DEFAULT_ADMIN_ROLE() returns bytes32 = 0x00;
definition MANAGE_MEMBERS_AND_QUORUM_ROLE() returns bytes32 = 0x66a484cf1a3c6ef8dfd59d24824943d2853a29d96f34a01271efc55774452a51; //keccak256("MANAGE_MEMBERS_AND_QUORUM_ROLE");
definition DISABLE_CONSENSUS_ROLE() returns bytes32 = 0x10b016346186602d93fc7a27ace09ba944baf9453611b186d36acd3d3d667dc0; //keccak256("DISABLE_CONSENSUS_ROLE");
definition MANAGE_FRAME_CONFIG_ROLE() returns bytes32 = 0x921f40f434e049d23969cbe68d9cf3ac1013fbe8945da07963af6f3142de6afe; //keccak256("MANAGE_FRAME_CONFIG_ROLE");
definition MANAGE_FAST_LANE_CONFIG_ROLE() returns bytes32 = 0x4af6faa30fabb2c4d8d567d06168f9be8adb583156c1ecb424b4832a7e4d6717; //keccak256("MANAGE_FAST_LANE_CONFIG_ROLE");
definition MANAGE_REPORT_PROCESSOR_ROLE() returns bytes32 = 0xc5219a8d2d0107a57aad00b22081326d173df87bad251126f070df2659770c3e; //keccak256("MANAGE_REPORT_PROCESSOR_ROLE");
// definition MANAGE_CONSENSUS_CONTRACT_ROLE() returns bytes32 = 0x04a0afbbd09d5ad397fc858789da4f8edd59f5ca5098d70faa490babee945c3b; //keccak256("MANAGE_CONSENSUS_CONTRACT_ROLE");
// definition MANAGE_CONSENSUS_VERSION_ROLE() returns bytes32 = 0xc31b1e4b732c5173dc51d519dfa432bad95550ecc4b0f9a61c2a558a2a8e4341; //keccak256("MANAGE_CONSENSUS_VERSION_ROLE");
// definition SUBMIT_DATA_ROLE() returns bytes32 = 0x65fa0c17458517c727737e4153dd477fa3e328cf706640b0f68b1a285c5990da; //keccak256("SUBMIT_DATA_ROLE");
definition UNREACHABLE_QUORUM() returns uint256 = max_uint256; // type(uint256).max
definition ZERO_HASH() returns bytes32 = 0; // bytes32(0)


// rule ideas for HashConsensus (without inheritance):
// ------------------------------------------------------------------------------------------
//  external non-view functions: setFrameConfig(), setFastLaneLengthSlots(), addMember(), removeMember(),
//                               setQuorum(), disableConsensus(), setReportProcessor(), submitReport()
//  external view functions    : getChainConfig(), getFrameConfig(), getCurrentFrame(),
//                               getIsMember(), getIsFastLaneMember(), getMembers(), getFastLaneMembers(),
//                               getQuorum(), getConsensusState(), getReportVariants(), getConsensusStateForMember()
//  definitions                : MANAGE_MEMBERS_AND_QUORUM_ROLE
//                               DISABLE_CONSENSUS_ROLE, MANAGE_FRAME_CONFIG_ROLE,
//                               MANAGE_FAST_LANE_CONFIG_ROLE, MANAGE_REPORT_PROCESSOR_ROLE,
//                               SLOTS_PER_EPOCH, SECONDS_PER_SLOT, GENESIS_TIME,
//                               UNREACHABLE_QUORUM, ZERO_HASH
//  storage slots (state vars) : _frameConfig, _memberStates, _memberAddresses, _memberIndices1b,
//                               _reportingState, _quorum, _reportVariants, _reportVariantsLength,
//                               _reportProcessor

//  1. All the external view functions cannot revert under any circumstance,
//     especially getCurrentFrame() as it is used by LegacyOracle and BaseOracle
//  2. Only ACL roles can call the external non-view functions:
//      setFrameConfig() - MANAGE_FRAME_CONFIG_ROLE 
//      setFastLaneLengthSlots() - MANAGE_FAST_LANE_CONFIG_ROLE
//      addMember() - MANAGE_MEMBERS_AND_QUORUM_ROLE
//      removeMember() - MANAGE_MEMBERS_AND_QUORUM_ROLE
//      setQuorum() - MANAGE_MEMBERS_AND_QUORUM_ROLE, DISABLE_CONSENSUS_ROLE (only if disabling it)
//      disableConsensus() - MANAGE_MEMBERS_AND_QUORUM_ROLE, DISABLE_CONSENSUS_ROLE
//      setReportProcessor() - MANAGE_REPORT_PROCESSOR_ROLE
//      submitReport() - only if getIsMember(msg.sender) == true
//  3. setFrameConfig() updates epochsPerFrame in a way that either keeps the current reference slot
//     the same or increases it by at least the minimum of old and new frame sizes
//  4. setFastLaneLengthSlots() works as expected, setting it to zero disables the fast lane subset
//     verify with getFrameConfig() and check that fastLaneLengthSlots < frameConfig.epochsPerFrame * SLOTS_PER_EPOCH
//  5. addMember() - cannot add an existing member
//  6. addMember() - cannot add an empty address as a member
//  7, addMember() - adding a member does not remove any other member
//  8. addMember() - adding a member increases the total members by 1
//  9. removeMember() - cannot remove a member that does not exists - reverts
// 10. removeMember() - removing a member does not remove any other member
// 11. removeMember() - removing a member decreases the total members by 1
// 12. setQuorum() - acts as expectedly, verified by getQuorum()
// 13. disableConsensus() - acts as expectedly, verified by getQuorum()
// 14. setReportProcessor() - cannot set an empty address
// 15. submitReport() - slot > max_uint64 => revert
// 16. submitReport() - slot < currentRefSlot => revert
// 17. submitReport() - slot <= lastProcessingRefSlot => revert
// 18. submitReport() - reportHash == 0 => revert
// 19. submitReport() - consensusVersion != getConsensusVersion() => revert
// 20. submitReport() - verify that _computeTimestampAtSlot(frame.reportProcessingDeadlineSlot) > TimeOf(frame.refSlot)
//                             that the deadline is explicitly == TimeOf(refslot+FrameSize)
// 21. submitReport() - revert if same oracle reports the same slot+hash (cannot double vote for same report)
// 22. submitReport() - single call to submit report increases only one support for one variant
//                      sum of supports of all variants < total members,
//                      because if Oracle member changes its mind, its previous support is removed
// 23. submitReport() - all variants should be removed when new frame starts


//  1. All the external view functions cannot revert under any circumstance,
//     especially getCurrentFrame() as it is used by LegacyOracle and BaseOracle
// Status: Fail
// https://vaas-stg.certora.com/output/80942/985192ce8baf4725a8b6d29c1d0dc2af/?anonymousKey=f2574e5803ece9f5b8d734ecd68b1d9ac714c1d5
rule viewFunctionsDoNotRevert(method f)
    filtered { f -> f.isView }
{
    env e; calldataarg args;

    require e.msg.value == 0; // view functions revert is you send eth

    f@withrevert(e,args);
    assert !lastReverted;
}

/// POTENTIAL ISSUE: SLOTS_PER_EPOCH, SECONDS_PER_SLOT, GENESIS_TIME can all be set to zero at constructor
/// if the above are zero => getCurrentFrame() will revert
// focus only on getCurrentFrame() and verify it does not revert
// Status: Timeout! (without simplification)
// https://vaas-stg.certora.com/output/80942/899cc6d765c7467c9e2af018ccca2ca5/?anonymousKey=ca1152175e66f3e61e7d2bffaded5098c62c3bbe
// Status: Pass (with simplification)
// https://vaas-stg.certora.com/output/80942/01ca967565ee4fc58101e7037160aaa1/?anonymousKey=fd302ac936356aa223eb706d466eeae5de7a155f
rule getCurrentFrameDoesNotRevert() {
    env e; calldataarg args;

    require e.msg.value == 0;                       // view functions revert is you send eth
    require e.block.timestamp > 1672531200;         // 01.01.2023 00:00:00
    require e.block.timestamp < 2524608000;         // 01.01.2050 00:00:00

    uint256 slotsPerEpoch; uint256 secondsPerSlot; uint256 genesisTime;
    slotsPerEpoch, secondsPerSlot, genesisTime = getChainConfig(e);

    require slotsPerEpoch > 0;                      // must be required at constructor
    require slotsPerEpoch == 1;                     // simplification
    require secondsPerSlot > 0;                     // must be required at constructor
    require secondsPerSlot == 1;                    // simplification
    require genesisTime < e.block.timestamp;        // must be required at constructor

    uint256 initialEpoch; uint256 epochsPerFrame; uint256 fastLaneLengthSlots;
    initialEpoch, epochsPerFrame, fastLaneLengthSlots = getFrameConfig(e);
    require epochsPerFrame > 0;                     // constructor already ensures this
    require epochsPerFrame < 31536000;              // assuming less than 1 year per frame

    // assuming correct configuration of the frame, otherwise revert
    require initialEpoch < (e.block.timestamp - genesisTime) / (secondsPerSlot * slotsPerEpoch);
    require initialEpoch > 0;                       // must be required at constructor
    // If initialEpoch == 0: revert! (line 545 in HashConsensus.sol), see run below:
    // https://vaas-stg.certora.com/output/80942/8b0204bf08e141d88d92e71d7e2bc653/?anonymousKey=f687713b6e337e389628a70e970ec0dc47477838

    // _computeSlotAtTimestamp:    (timestamp - GENESIS_TIME) / SECONDS_PER_SLOT
    // _computeEpochAtSlot:        slot / SLOTS_PER_EPOCH;

    getCurrentFrame@withrevert(e,args);
    assert !lastReverted;
}

//  2. Only ACL roles can call the external non-view functions:
//      setFrameConfig() - MANAGE_FRAME_CONFIG_ROLE 
//      setFastLaneLengthSlots() - MANAGE_FAST_LANE_CONFIG_ROLE
//      addMember() - MANAGE_MEMBERS_AND_QUORUM_ROLE
//      removeMember() - MANAGE_MEMBERS_AND_QUORUM_ROLE
//      setQuorum() - MANAGE_MEMBERS_AND_QUORUM_ROLE, DISABLE_CONSENSUS_ROLE (only if disabling it)
//      disableConsensus() - MANAGE_MEMBERS_AND_QUORUM_ROLE, DISABLE_CONSENSUS_ROLE
//      setReportProcessor() - MANAGE_REPORT_PROCESSOR_ROLE
//      submitReport() - only if getIsMember(msg.sender) == true
// Status: Fail (partially) because some functions can be called by more than one role
// The verification will be done per function in separate rules
// https://vaas-stg.certora.com/output/80942/b0aebafd7b554b3882fe688da319b9ba/?anonymousKey=4361d0b5bbd895ea4d92beeb16e0deda7cd095c7
rule onlyAllowedRoleCanCallMethod(method f) 
    filtered { f -> !f.isView }
{
    env e; calldataarg args;

    bytes32 roleR;
    bool hasRoleR = hasRole(e,roleR,e.msg.sender);
    require hasRoleR == false;

    bytes32 roleRAdmin = getRoleAdmin(e,roleR);
    bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);
    require isAdmin == false;

    bool isMember = getIsMember(e,e.msg.sender);
    require isMember == false;

    f@withrevert(e,args);
    bool callReverted = lastReverted;

    assert ((f.selector == setFrameConfig(uint256,uint256).selector) &&
            roleR == MANAGE_FRAME_CONFIG_ROLE()) => lastReverted;
    
    assert ((f.selector == setFastLaneLengthSlots(uint256).selector) &&
            roleR == MANAGE_FAST_LANE_CONFIG_ROLE()) => lastReverted;
    
    assert ((f.selector == addMember(address,uint256).selector) &&
            roleR == MANAGE_MEMBERS_AND_QUORUM_ROLE()) => lastReverted;
    
    assert ((f.selector == removeMember(address,uint256).selector) &&
            roleR == MANAGE_MEMBERS_AND_QUORUM_ROLE()) => lastReverted;

    assert ((f.selector == setQuorum(uint256).selector) &&
            roleR == MANAGE_MEMBERS_AND_QUORUM_ROLE()) => lastReverted;
    
    assert ((f.selector == disableConsensus().selector) &&
            roleR == MANAGE_MEMBERS_AND_QUORUM_ROLE()) => lastReverted;
    
    assert ((f.selector == setReportProcessor(address).selector) &&
            roleR == MANAGE_REPORT_PROCESSOR_ROLE()) => lastReverted;
    
    assert (f.selector == submitReport(uint256,bytes32,uint256).selector) => lastReverted;

    //assert (!hasRoleRBefore && hasRoleRAfter) => (isAdmin); 
}


// 3a. setFrameConfig() ACL check
// Status: Pass
// https://vaas-stg.certora.com/output/80942/af309b535e244a3ca748f0b80f4f301c/?anonymousKey=a0280547905d76770006b8415c1340d089a21f75
rule setFrameConfigACL() {
    env e; calldataarg args;

    bytes32 roleR = MANAGE_FRAME_CONFIG_ROLE();
    bool hasRoleR = hasRole(e,roleR,e.msg.sender);

    bytes32 roleRAdmin = getRoleAdmin(e,roleR);
    bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);

    uint256 epochsPerFrame; uint256 fastLaneLengthSlots;
    setFrameConfig@withrevert(e, epochsPerFrame, fastLaneLengthSlots);
    bool callReverted = lastReverted;

    assert (!hasRoleR && !isAdmin) => callReverted;
}

//  3. setFrameConfig() updates epochsPerFrame in a way that either keeps the current reference slot
//     the same or increases it by at least the minimum of old and new frame sizes
// Status: Fails (need to work on)
// https://vaas-stg.certora.com/output/80942/b8aa709fcefc4b2bb039c2513f17ddd6/?anonymousKey=a19462454ae831311d10d01fdd3a7f4dbe331812
rule setFrameConfigCorrectness() {
    saneTimeConfig();           // ensuring sane chainConfig and frameConfig
    env e; calldataarg args;

    // Get state before
    uint256 refSlot1; uint256 reportProcessingDeadlineSlot1;
    refSlot1, reportProcessingDeadlineSlot1 = getCurrentFrame(e);
    
    uint256 initialEpoch1; uint256 epochsPerFrame1; uint256 fastLaneLengthSlots1;
    initialEpoch1, epochsPerFrame1, fastLaneLengthSlots1 = getFrameConfig(e);

    uint256 epochsPerFrame; uint256 fastLaneLengthSlots;
    setFrameConfig(e, epochsPerFrame, fastLaneLengthSlots);

    // Get state after
    uint256 refSlot2; uint256 reportProcessingDeadlineSlot2;
    refSlot2, reportProcessingDeadlineSlot2 = getCurrentFrame(e);

    uint256 initialEpoch2; uint256 epochsPerFrame2; uint256 fastLaneLengthSlots2;
    initialEpoch2, epochsPerFrame2, fastLaneLengthSlots2 = getFrameConfig(e);

    // verify getter returns updated values
    assert epochsPerFrame == epochsPerFrame2;
    assert fastLaneLengthSlots == fastLaneLengthSlots2;

    // verify the comment of the function:
    // keeps the current reference slot the same or
    // increases it by at least the minimum of old and new frame sizes
    uint256 slotsPerEpoch; uint256 secondsPerSlot; uint256 genesisTime;
    slotsPerEpoch, secondsPerSlot, genesisTime = getChainConfig(e);

    assert (epochsPerFrame2 >= epochsPerFrame1) =>
                (refSlot1 == refSlot2) || (refSlot2 >= refSlot1 + epochsPerFrame1 * slotsPerEpoch);
    
    assert (epochsPerFrame2 <= epochsPerFrame1) =>
                (refSlot1 == refSlot2) || (refSlot2 >= refSlot1 + epochsPerFrame2 * slotsPerEpoch);
}








// // rule ideas for AccountingOracle (without inheritance):
// // ------------------------------------------------------------------------------------------
// //  external non-view functions: initialize(), initializeWithoutMigration(), submitReportData(),
// //                               submitReportExtraDataEmpty(), submitReportExtraDataList()
// //  definitions                : SUBMIT_DATA_ROLE
// //                               EXTRA_DATA_TYPE_STUCK_VALIDATORS, EXTRA_DATA_TYPE_EXITED_VALIDATORS
// //                               EXTRA_DATA_FORMAT_EMPTY, EXTRA_DATA_FORMAT_LIST
// //  storage slots (state vars) : EXTRA_DATA_PROCESSING_STATE_POSITION
// // 
// //  1. verify all the reverting scenarios of submitReportData():
// //     a) The caller is not a member of the oracle committee and doesn't possess the SUBMIT_DATA_ROLE.
// //     b) The provided contract version is different from the current one.
// //     c) The provided consensus version is different from the expected one.
// //     d) The provided reference slot differs from the current consensus frame's one.
// //     e) The processing deadline for the current consensus frame is missed.
// //     f) The keccak256 hash of the ABI-encoded data is different from the last hash provided by the hash consensus contract.
// //     g) The provided data doesn't meet safety checks. (in OracleReportSanityChecker.sol)
// //  5. If ReportData.extraDataFormat is not EXTRA_DATA_FORMAT_EMPTY=0 or EXTRA_DATA_FORMAT_LIST=1 => revert
// //  6a.if the oracle report contains no extra data => ReportData.extraDataHash == 0
// //  6b.if the oracle report contains extra data => ReportData.extraDataHash != 0
// //  7a.if the oracle report contains no extra data => ReportData.extraDataItemsCount == 0
// //  7b.if the oracle report contains extra data => ReportData.extraDataItemsCount != 0
// //  8a.submitReportData(), submitReportExtraDataList(), submitReportExtraDataEmpty
// //     can be called only if msg.sender has the appropriate role SUBMIT_DATA_ROLE (same as 1a)
// //     or if the caller is a member of the oracle committee
// //  4. cannot submit reports (Data/ExtraDataList/Empty) twice in the same e.block.timestamp
// // 11. TODO: If the extraDataReport was processed successfully for specific refSlot, you can not submit another report for the same refSlot
// // 12. TODO: If the extraDataReport was processed
// //  9. Cannot initialize() or initializeWithoutMigration() twice
// // 10. Cannot initialize() with empty addresses

// //  still needs to work on:
// //  2. verify submitReportData() does not revert outside of the allowed reverting scenarios (? - how?)
// //  3. verify all the errors on lines 91-110 are caught correctly (? - probably duplicates point 1 above)


// //  1. verify all the reverting scenarios of submitReportData()
// //  5. If ReportData.extraDataFormat is not EXTRA_DATA_FORMAT_EMPTY=0 or EXTRA_DATA_FORMAT_LIST=1 => revert
// //  6a.if the oracle report contains no extra data => ReportData.extraDataHash == 0
// //  6b.if the oracle report contains extra data => ReportData.extraDataHash != 0
// //  7a.if the oracle report contains no extra data => ReportData.extraDataItemsCount == 0
// //  7b.if the oracle report contains extra data => ReportData.extraDataItemsCount != 0
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/bd32307a5a324b2881652d1b2258b601/?anonymousKey=b7d045ddc841e27f4a8eea9a7065d7edc0f3ce26
// rule correctRevertsOfSubmitReportData() {
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     bool hasSubmitDataRole = hasRole(e,SUBMIT_DATA_ROLE(),e.msg.sender);
//     bool callerIsConsensusMember = isConsensusMember(e,e.msg.sender);

//     uint256 currentContractVersion = getContractVersion(e);
//     uint256 currentConsensusVersion = getConsensusVersion(e);

//     bytes32 currentHash; uint256 currentRefSlot; uint256 currentDeadline; bool processingStarted;
//     currentHash, currentRefSlot, currentDeadline, processingStarted = getConsensusReport(e);

//     uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e);

//     // struct ReportData
//     uint256 consensusVersion; uint256 refSlot;
//     // uint256 numValidators; uint256 clBalanceGwei;
//     // uint256[] stakingModuleIdsWithNewlyExitedValidators; uint256[] numExitedValidatorsByStakingModule;
//     // uint256 withdrawalVaultBalance; uint256 elRewardsVaultBalance;
//     uint256 lastFinalizableWithdrawalRequestId; uint256 simulatedShareRate; bool isBunkerMode;
//     uint256 extraDataFormat; bytes32 extraDataHash; uint256 extraDataItemsCount;

//     uint256 contractVersion;

//     bytes32 submittedHash = helperCreateAndSubmitReportData@withrevert( e,
//                                 consensusVersion, refSlot,
//                                 lastFinalizableWithdrawalRequestId, simulatedShareRate, isBunkerMode,
//                                 extraDataFormat, extraDataHash, extraDataItemsCount,
//                                 contractVersion );
    
//     bool submitReverted = lastReverted;

//     assert (!hasSubmitDataRole && !callerIsConsensusMember) => submitReverted;  // case 1a
//     assert (contractVersion != currentContractVersion)      => submitReverted;  // case 1b
//     assert (consensusVersion != currentConsensusVersion)    => submitReverted;  // case 1c
//     assert (refSlot != currentRefSlot)                      => submitReverted;  // case 1d
//     assert (e.block.timestamp > currentDeadline)            => submitReverted;  // case 1e
//     assert (submittedHash != currentHash)                   => submitReverted;  // case 1f

//     assert (extraDataFormat != EXTRA_DATA_FORMAT_EMPTY() &&
//             extraDataFormat != EXTRA_DATA_FORMAT_LIST())    => submitReverted;  // case 5
    
//     assert (extraDataFormat == EXTRA_DATA_FORMAT_EMPTY() && 
//             extraDataHash != 0)                             => submitReverted;  // case 6a
    
//     assert (extraDataFormat == EXTRA_DATA_FORMAT_LIST() && 
//             extraDataHash == 0)                             => submitReverted;  // case 6b
    
//     assert (extraDataFormat == EXTRA_DATA_FORMAT_EMPTY() && 
//             extraDataItemsCount != 0)                       => submitReverted;  // case 7a
    
//     assert (extraDataFormat == EXTRA_DATA_FORMAT_LIST() && 
//             extraDataItemsCount == 0)                       => submitReverted;  // case 7b
// }

// //  8a.submitReportData(), submitReportExtraDataList(), submitReportExtraDataEmpty
// //     can be called only if msg.sender has the appropriate role SUBMIT_DATA_ROLE (same as 1a)
// //     or if the caller is a member of the oracle committee
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/f4905a42c92847038aa32718403b9c8a/?anonymousKey=7bd858eae6586c20777b7c372fa7dec65ce0ed87
// rule callerMustHaveSubmitDataRoleOrBeAConsensusMember(method f) 
//     filtered { f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector ||
//                     f.selector == submitReportExtraDataList(bytes).selector ||
//                     f.selector == submitReportExtraDataEmpty().selector }
// {    
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     bool hasSubmitDataRole = hasRole(e,SUBMIT_DATA_ROLE(),e.msg.sender);
//     bool callerIsConsensusMember = isConsensusMember(e,e.msg.sender);

//     f(e,args);

//     assert (!hasSubmitDataRole && !callerIsConsensusMember) => lastReverted;
// }

// //  4. cannot submit reports (Data/ExtraDataList/Empty) twice in the same e.block.timestamp
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/a468b233b03f4f8d8382141d1d0a6eb6/?anonymousKey=f2e33c53956a1dea740d260ea93a234b0fdc8af4
// rule cannotSubmitReportDataTwiceAtSameTimestamp(method f) 
//     filtered { f -> f.selector == submitReportData((uint256,uint256,uint256,uint256,uint256[],uint256[],uint256,uint256,uint256,uint256,bool,uint256,bytes32,uint256),uint256).selector ||
//                     f.selector == submitReportExtraDataList(bytes).selector ||
//                     f.selector == submitReportExtraDataEmpty().selector }
// {    
//     require contractAddressesLinked();
//     env e; calldataarg args; env e2; calldataarg args2;

//     require e.block.timestamp == e2.block.timestamp;

//     f(e,args);              // successfully submit a report at time == e.block.timestamp
//     f@withrevert(e2,args2); // same e.block.timestamp, any calldataarg

//     assert lastReverted;
// }

// //  9. Cannot initialize() or initializeWithoutMigration() twice
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/e04fba855b5641f682cb05edb5362213/?anonymousKey=163260b76cb1479de139f7b547b37bea891bfccb
// rule cannotInitializeTwice(method f) 
//     filtered { f -> f.selector == initialize(address,address,uint256).selector ||
//                     f.selector == initializeWithoutMigration(address,address,uint256,uint256).selector }
// {    
//     require contractAddressesLinked();
//     env e; calldataarg args;
//     env e2; calldataarg args2;

//     f(e,args);
//     f@withrevert(e2,args2);

//     assert lastReverted;
// }

// // 10. Cannot initialize() with empty addresses
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/f264880cd2dd4d0381fdaa06a5234879/?anonymousKey=511229de14f62dab5a22416abd33943fb8b5e538
// // if both directions <=> then status: fail
// // https://vaas-stg.certora.com/output/80942/622251a95a63420490af941bc010d4ac/?anonymousKey=ea15d59a3222d319a1c85f86159cc315c4e74695
// rule cannotInitializeWithEmptyAddresses() {
//     require contractAddressesLinked();
//     env e; calldataarg args;
//     // require e.msg.value == 0;

//     address admin; address consensusContract; uint256 consensusVersion;
//     initialize@withrevert(e, admin, consensusContract, consensusVersion);

//     assert (admin == 0 || consensusContract == 0) => lastReverted;
// }

// // rules for BaseOracle.sol:
// // ------------------------------------------------------------------------------------------
// //  external non-view functions: setConsensusVersion(), setConsensusContract(),
// //                               submitConsensusReport()
// //  definitions                : MANAGE_CONSENSUS_CONTRACT_ROLE, MANAGE_CONSENSUS_VERSION_ROLE
// //  storage slots (state vars) : CONSENSUS_CONTRACT_POSITION, CONSENSUS_VERSION_POSITION
// //                               LAST_PROCESSING_REF_SLOT_POSITION, CONSENSUS_REPORT_POSITION
// // 
// // 1a.setConsensusContract() can be called only if msg.sender has the appropriate role
// // 1b.setConsensusVersion() can be called only if msg.sender has the appropriate role
// // 2. Only Consensus contract can submit a report, i.e., call submitConsensusReport()
// // 3. Cannot submitConsensusReport() if its refSlot < prevSubmittedRefSlot
// // 4. Cannot submitConsensusReport() if its refSlot <= prevProcessingRefSlot
// // 5. Cannot submitConsensusReport() if its deadline <= refSlot
// // 6. Cannot submitConsensusReport() if its reportHash == 0

// // 1a.setConsensusContract() can be called only if msg.sender has the appropriate role
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/0e9e4a93a81945f3ac7dfc60d531817c/?anonymousKey=506b7ea379db5fed22a8fbdfc81477bedcf25010
// rule onlyManagerCanSetConsensusContract() {
//     env e; calldataarg args;

//     bytes32 roleManager = MANAGE_CONSENSUS_CONTRACT_ROLE();
//     bool isManager = hasRole(e,roleManager,e.msg.sender);

//     bytes32 roleAdmin = getRoleAdmin(e,roleManager);
//     bool isAdmin = hasRole(e,roleAdmin,e.msg.sender);

//     address newAddress;
//     setConsensusContract@withrevert(e,newAddress);

//     assert (!isManager && !isAdmin) => lastReverted;
// }

// // 1b.setConsensusVersion() can be called only if msg.sender has the appropriate role
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/1dd3d3d2456441e5a4cb474b5f933881/?anonymousKey=250fe9c13081828347aaf5dedd477bb59f467554
// rule onlyManagerCanSetConsensusVersion() {
//     env e; calldataarg args;

//     bytes32 roleManager = MANAGE_CONSENSUS_VERSION_ROLE();
//     bool isManager = hasRole(e,roleManager,e.msg.sender);

//     bytes32 roleAdmin = getRoleAdmin(e,roleManager);
//     bool isAdmin = hasRole(e,roleAdmin,e.msg.sender);

//     uint256 newVersion;
//     setConsensusVersion@withrevert(e,newVersion);

//     assert (!isManager && !isAdmin) => lastReverted;
// }

// // 2. Only Consensus contract can submit a report, i.e., call submitConsensusReport()
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/12dc1ba7763b43a09054482acefef5e1/?anonymousKey=e3f6b40b6a126e42a5784249629cb5fc700c3cc2
// rule onlyConsensusContractCanSubmitConsensusReport(method f) 
//     filtered { f -> f.selector == submitConsensusReport(bytes32,uint256,uint256).selector }
// {    
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     f@withrevert(e,args);

//     assert (e.msg.sender != ConsensusContract) => lastReverted;
// }

// // 3. Cannot submitConsensusReport() if its refSlot < prevSubmittedRefSlot
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/d3493f0f47a544d086086b793689841c/?anonymousKey=e0006776f21a9ac59c4745a93d0a7e854c7c4e9a
// rule refSlotCannotDecrease() {    
//     require contractAddressesLinked();
//     env e; calldataarg args;  

//     uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e);

//     bytes32 prevSubmittedHash; uint256 prevSubmittedRefSlot;
//     uint256 prevSubmittedDeadline; bool processingStarted;
//     prevSubmittedHash, prevSubmittedRefSlot, prevSubmittedDeadline, processingStarted = getConsensusReport(e);

//     bytes32 reportHash; uint256 refSlot; uint256 deadline;
//     submitConsensusReport@withrevert(e, reportHash, refSlot, deadline);

//     assert (refSlot < prevSubmittedRefSlot) => lastReverted;
// }

// // 4. Cannot submitConsensusReport() if its refSlot <= prevProcessingRefSlot
// // As mentioned in IReportAsyncProcessor imported from HashConsensus.sol
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/ea835481700b428aa37c1b82b1ccac33/?anonymousKey=8f394d9d34b1bda2b007f90b7897952c5400a2f0
// rule refSlotMustBeGreaterThanProcessingOne() {    
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e);
    
//     bytes32 reportHash; uint256 refSlot; uint256 deadline;
//     submitConsensusReport@withrevert(e, reportHash, refSlot, deadline);

//     assert (refSlot <= lastProcessingRefSlot) => lastReverted;
// }

// // 5. Cannot submitConsensusReport() if its deadline <= refSlot
// // Status: Fail
// // https://vaas-stg.certora.com/output/80942/8c323c10f71b4dafb6b754ba1a4ec865/?anonymousKey=e4b06b987f42ac8c5f9088aa491740d37b475bde
// rule deadlineMustBeAfterRefSlotBaseOracle() {    
//     require contractAddressesLinked();
//     env e; calldataarg args;
    
//     bytes32 reportHash; uint256 refSlot; uint256 deadline;
//     submitConsensusReport@withrevert(e,reportHash, refSlot, deadline);

//     assert (deadline <= refSlot) => lastReverted;
// }

// // 6. Cannot submitConsensusReport() if its reportHash == 0
// // Status: Fail
// // https://vaas-stg.certora.com/output/80942/430b70d788dd453eae3647ac444f9cad/?anonymousKey=9f16b9986826770acb548c758fa681767ed4cabf
// rule reportHashCannotBeZero() {    
//     require contractAddressesLinked();
//     env e; calldataarg args;
    
//     bytes32 reportHash; uint256 refSlot; uint256 deadline;
//     submitConsensusReport@withrevert(e,reportHash, refSlot, deadline);

//     assert (reportHash == 0) => lastReverted;
// }


// /* passes but is wrongly written - delete
// // Status: Pass
// // new: https://vaas-stg.certora.com/output/80942/e03b0807e4bc40f18b097fb6261c3741/?anonymousKey=2b28ef31f55d6e50b58ee6e41622d1eeb2056690
// // old: https://vaas-stg.certora.com/output/80942/21cba2b81811458ea98ea5a12987aa4a/?anonymousKey=785d93a962710a832ff9f4ba0555d07554d2976b
// rule refSlotMustBeGreaterThanProcessingOne(method f) 
//     filtered { f -> f.selector == submitConsensusReport(bytes32,uint256,uint256).selector }
// {    
//     require contractAddressesLinked();
//     env e; calldataarg args;
//     env e1; calldataarg args1;
//     env e2; calldataarg args2;
//     require e.block.timestamp < e1.block.timestamp;  // time flow
//     require e1.block.timestamp < e2.block.timestamp; // time flow

//     submitReportData(e,args); // first submits a report successfully for processing

//     f(e1,args1); // then submits a consensus report successfully (still not processed)

//     bytes32 hash; uint256 refSlot; uint256 processingDeadlineTime; bool processingStarted;

//     hash, refSlot, processingDeadlineTime, processingStarted = getConsensusReport(e2);
//     uint256 lastProcessingRefSlot = getLastProcessingRefSlot(e2);

//     f@withrevert(e2,args2); // finally try to submit a new consensus report

//     // assert lastReverted; // FAIL --> checked that the above call is NOT always reverting
//     assert (refSlot <= lastProcessingRefSlot) => lastReverted;
// }
// */



// // rules for Versioned:


// // rules for UnstructuredStorage.sol:


// // rules for AccessControlEnumerable.sol
// // ------------------------------------------------------------------------------------------
// // 1. adding a new role member with roleR should *increase* the count of getRoleMemberCount(roleR) by one
// // 2. removing a roleR from a member should *decrease* the count of getRoleMemberCount(roleR) by one
// // 3. getRoleMemberCount(roleX) should not be affected by adding or removing roleR (roleR != roleX)

// // 1. adding a new role member with roleR should *increase* the count of getRoleMemberCount(roleR) by one
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// rule countIncreaseByOneWhenGrantRole(method f) {
//     require contractAddressesLinked();
//     env e; calldataarg args;
    
//     bytes32 roleR; address accountA;

//     renounceRole(e,roleR,accountA); // ensure accountA does not have roleR

//     bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
//     uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
//     require countRoleRMembersBefore < UINT256_MAX();  // reasonable there are not so many role members

//     // grantRole(e,roleR,accountA);
//     f(e,args);

//     bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
//     uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);

//     assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1;
//     /*
//     assert !hasRoleRAccountABefore;
//     assert hasRoleRAccountAAfter;
//     assert countRoleRMembersAfter - countRoleRMembersBefore == 1;
//     */
// }

// // 2. removing a roleR from a member should *decrease* the count of getRoleMemberCount(roleR) by one
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// rule countDecreaseByOneWhenRenounceRole(method f) {
//     require contractAddressesLinked();
//     env e; calldataarg args;
    
//     bytes32 roleR; address accountA;

//     grantRole(e,roleR,accountA); // ensure accountA has roleR

//     bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
//     uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
//     require countRoleRMembersBefore > 0;  // there is at least one account with roleR
    
//     // renounceRole(e,roleR,accountA);
//     f(e,args);

//     bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
//     uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);

//     assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => countRoleRMembersBefore - countRoleRMembersAfter == 1;
//     /*
//     assert hasRoleRAccountABefore;
//     assert !hasRoleRAccountAAfter;
//     assert countRoleRMembersBefore - countRoleRMembersAfter == 1;
//     */
// }

// // 3. getRoleMemberCount(roleX) should not be affected by adding or removing roleR (roleR != roleX)
// // If a member with roleR was added/removed, the count of members with roleX != roleR should not change
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// rule memberCountNonInterference(method f) {
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     bytes32 roleR; bytes32 roleX;

//     uint256 countRoleRMembersBefore = getRoleMemberCount(e,roleR);
//     uint256 countRoleXMembersBefore = getRoleMemberCount(e,roleX);

//     f(e,args);

//     uint256 countRoleRMembersAfter = getRoleMemberCount(e,roleR);
//     uint256 countRoleXMembersAfter = getRoleMemberCount(e,roleX);

//     require roleR != roleX;
    
//     assert (countRoleRMembersAfter > countRoleRMembersBefore) =>
//             countRoleXMembersAfter == countRoleXMembersBefore;

//     assert (countRoleRMembersAfter < countRoleRMembersBefore) =>
//             countRoleXMembersAfter == countRoleXMembersBefore;
// }

// // rules for AccessControl.sol:
// // ------------------------------------------------------------------------------------------
// // 1. only admin of role R can grant the role R to the account A (role R can be any role including the admin role)
// // 2. only admin or the account A itself can revoke the role R of account A (no matter the role)
// // 3. granting or revoking roleR from accountA should not affect any accountB

// // 1. only admin of role R can grant the role R to the account A (role R can be any role including the admin role)
// // Status: Fails
// // https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// rule onlyAdminCanGrantRole(method f) {
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     bytes32 roleR; address accountA;
//     bool hasRoleRBefore = hasRole(e,roleR,accountA);

//     bytes32 roleRAdmin = getRoleAdmin(e,roleR);
//     bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);

//     f(e,args);

//     bool hasRoleRAfter = hasRole(e,roleR,accountA);

//     assert (!hasRoleRBefore && hasRoleRAfter) => (isAdmin); 
// }

// // 2. only admin or the account A itself can revoke the role R of account A (no matter the role)
// // Status: Pass
// // https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// rule onlyAdminOrSelfCanRevokeRole(method f) {
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     bytes32 roleR; address accountA;
//     bool hasRoleRBefore = hasRole(e,roleR,accountA);

//     bytes32 roleRAdmin = getRoleAdmin(e,roleR);
//     bool isAdmin = hasRole(e,roleRAdmin,e.msg.sender);

//     f(e,args);

//     bool hasRoleRAfter = hasRole(e,roleR,accountA);

//     assert (hasRoleRBefore && !hasRoleRAfter) => (isAdmin || e.msg.sender == accountA); 
// }

// // 3. granting or revoking roleR from accountA should not affect any accountB
// // Status: Pass
// // Note: had to comment line 315 in BaseOracle.sol (to resolve the getProcessingState() dispatcher problem)
// // https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
// rule nonInterferenceOfRolesAndAccounts(method f) {
//     require contractAddressesLinked();
//     env e; calldataarg args;

//     bytes32 roleR; address accountA;
//     bytes32 roleX; address accountB;

//     bool hasRoleRAccountABefore = hasRole(e,roleR,accountA);
//     bool hasRoleXAccountBBefore = hasRole(e,roleX,accountB);

//     f(e,args);

//     bool hasRoleRAccountAAfter = hasRole(e,roleR,accountA);
//     bool hasRoleXAccountBAfter = hasRole(e,roleX,accountB);

//     require (roleR != roleX) && (accountA != accountB);

//     assert (!hasRoleRAccountABefore && hasRoleRAccountAAfter) => 
//             (hasRoleXAccountBBefore && hasRoleXAccountBAfter) || 
//             (!hasRoleXAccountBBefore && !hasRoleXAccountBAfter);
    
//     assert (hasRoleRAccountABefore && !hasRoleRAccountAAfter) => 
//             (hasRoleXAccountBBefore && hasRoleXAccountBAfter) || 
//             (!hasRoleXAccountBBefore && !hasRoleXAccountBAfter);
// }


/**************************************************
 *                   MISC Rules                   *
 **************************************************/

// Status: Fails (as expected, no issues)
// https://vaas-stg.certora.com/output/80942/ea773d7513c64b3eb13469903a91dbbc/?anonymousKey=7c4acab781c5df59e5a45ffae8c7d442f3643323
rule sanity(method f) 
filtered { f -> !f.isView }
{
    //require contractAddressesLinked();
    env e; calldataarg args;

    f(e,args);
    assert false;
}