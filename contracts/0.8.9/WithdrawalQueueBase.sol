// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0

/* See contracts/COMPILERS.md */
pragma solidity 0.8.9;

import "@openzeppelin/contracts-v4.4/utils/structs/EnumerableSet.sol";
import {UnstructuredStorage} from "./lib/UnstructuredStorage.sol";
import {UnstructuredRefStorage} from "./lib/UnstructuredRefStorage.sol";
import {Math} from "./lib/Math.sol";

/// @title Queue to store and manage WithdrawalRequests.
/// @dev Use an optimizations to store discounts heavily inspired
/// by Aragon MiniMe token https://github.com/aragon/aragon-minime/blob/master/contracts/MiniMeToken.sol
///
/// @author folkyatina
abstract contract WithdrawalQueueBase {
    using EnumerableSet for EnumerableSet.UintSet;
    using UnstructuredStorage for bytes32;
    using UnstructuredRefStorage for bytes32;

    /// @notice precision base for share rate and discounting factor values in the contract
    uint256 internal constant E27_PRECISION_BASE = 1e27;

    uint256 internal constant MAX_EXTREMA_PER_CALL = 36;
    uint256 internal constant MAX_REQUESTS_PER_CALL = 1000;

    uint256 internal constant SHARE_RATE_UNLIMITED = type(uint256).max;

    /// @dev return value for the `find...` methods in case of no result
    uint256 internal constant NOT_FOUND = 0;

    // queue for withdrawal requests, indexes (requestId) start from 1
    bytes32 internal constant QUEUE_POSITION = keccak256("lido.WithdrawalQueue.queue");
    // length of the queue
    bytes32 internal constant LAST_REQUEST_ID_POSITION = keccak256("lido.WithdrawalQueue.lastRequestId");
    // length of the finalized part of the queue. Always <= `requestCounter`
    bytes32 internal constant LAST_FINALIZED_REQUEST_ID_POSITION =
        keccak256("lido.WithdrawalQueue.lastFinalizedRequestId");
    /// finalization discount history, indexes start from 1
    bytes32 internal constant CHECKPOINTS_POSITION = keccak256("lido.WithdrawalQueue.checkpoints");
    /// length of the checkpoints
    bytes32 internal constant LAST_CHECKPOINT_INDEX_POSITION = keccak256("lido.WithdrawalQueue.lastCheckpointIndex");
    /// amount of eth locked on contract for withdrawal
    bytes32 internal constant LOCKED_ETHER_AMOUNT_POSITION = keccak256("lido.WithdrawalQueue.lockedEtherAmount");
    /// withdrawal requests mapped to the owners
    bytes32 internal constant REQUEST_BY_OWNER_POSITION = keccak256("lido.WithdrawalQueue.requestsByOwner");
    /// list of extremum requests for shareRate(request_id) function
    bytes32 internal constant EXTREMA_POSITION = keccak256("lido.WithdrawalQueue.extrema");
    /// last extreum index that was already checked for finalization
    bytes32 internal constant LAST_CHECKED_EXTREMUM_POSITION = keccak256("lido.WithdrawalQueue.lastCheckedExtremum");

    bytes32 internal constant LAST_REPORT_TIMESTAMP_POSITION = keccak256("lido.WithdrawalQueue.lastReportTimestamp");


    /// @notice structure representing a request for withdrawal.
    struct WithdrawalRequest {
        /// @notice sum of the all stETH submitted for withdrawals up to this request
        uint128 cumulativeStETH;
        /// @notice sum of the all shares locked for withdrawal up to this request
        uint128 cumulativeShares;
        /// @notice address that can claim or transfer the request
        address owner;
        /// @notice block.timestamp when the request was created
        uint40 timestamp;
        /// @notice flag if the request was claimed
        bool claimed;
        /// @notice timestamp of lastReport
        uint40 reportTimestamp;
    }

    /// @notice structure to store discounts for requests that are affected by negative rebase
    struct Checkpoint {
        uint256 fromRequestId;
        uint256 maxShareRate;
    }

    /// @notice output format struct for `_getWithdrawalStatus()` method
    struct WithdrawalRequestStatus {
        /// @notice stETH token amount that was locked on withdrawal queue for this request
        uint256 amountOfStETH;
        /// @notice amount of stETH shares locked on withdrawal queue for this request
        uint256 amountOfShares;
        /// @notice address that can claim or transfer this request
        address owner;
        /// @notice timestamp of when the request was created, in seconds
        uint256 timestamp;
        /// @notice true, if request is finalized
        bool isFinalized;
        /// @notice true, if request is claimed. Request is claimable if (isFinalized && !isClaimed)
        bool isClaimed;
    }

    /// @dev Contains both stETH token amount and its corresponding shares amount
    event WithdrawalRequested(
        uint256 indexed requestId,
        address indexed requestor,
        address indexed owner,
        uint256 amountOfStETH,
        uint256 amountOfShares
    );
    event WithdrawalBatchFinalized(
        uint256 indexed from, uint256 indexed to, uint256 amountOfETHLocked, uint256 sharesToBurn, uint256 timestamp
    );
    event WithdrawalClaimed(
        uint256 indexed requestId, address indexed owner, address indexed receiver, uint256 amountOfETH
    );

    error ZeroAmountOfETH();
    error ZeroShareRate();
    error ZeroTimestamp();
    error TooMuchEtherToFinalize(uint256 sent, uint256 maxExpected);
    error NotOwner(address _sender, address _owner);
    error InvalidRequestId(uint256 _requestId);
    error InvalidRequestIdRange(uint256 startId, uint256 endId);
    error InvalidState();
    error InvalidBatches();
    error EmptyBatches();
    error RequestNotFoundOrNotFinalized(uint256 _requestId);
    error NotEnoughEther();
    error RequestAlreadyClaimed(uint256 _requestId);
    error InvalidHint(uint256 _hint);
    error CantSendValueRecipientMayHaveReverted();

    /// @notice id of the last request, returns 0, if no request in the queue
    function getLastRequestId() public view returns (uint256) {
        return LAST_REQUEST_ID_POSITION.getStorageUint256();
    }

    /// @notice id of the last finalized request, returns 0 if no finalized requests in the queue
    function getLastFinalizedRequestId() public view returns (uint256) {
        return LAST_FINALIZED_REQUEST_ID_POSITION.getStorageUint256();
    }

    /// @notice amount of ETH on this contract balance that is locked for withdrawal and available to claim
    function getLockedEtherAmount() public view returns (uint256) {
        return LOCKED_ETHER_AMOUNT_POSITION.getStorageUint256();
    }

    /// @notice length of the checkpoints. Last possible value for the claim hint
    function getLastCheckpointIndex() public view returns (uint256) {
        return LAST_CHECKPOINT_INDEX_POSITION.getStorageUint256();
    }

    /// @notice return the number of unfinalized requests in the queue
    function unfinalizedRequestNumber() external view returns (uint256) {
        return getLastRequestId() - getLastFinalizedRequestId();
    }

    /// @notice Returns the amount of stETH in the queue yet to be finalized
    function unfinalizedStETH() external view returns (uint256) {
        return
            _getQueue()[getLastRequestId()].cumulativeStETH - _getQueue()[getLastFinalizedRequestId()].cumulativeStETH;
    }

    // FINALIZATION.
    // Process when protocol is fixing the withdrawal request value and lock the required amount of stETH.
    // It is driven by the oracle report
    // Right now finalization consists of several steps:
    // 1. Oracle daemon precalculates finalization batches' boundaries that is valid on oracle report refSlot
    //  and post it with the report - `calculateFinalizationBatches()`
    // 2. Lido contract invokes `onPreRebase()` handler to update ShareRate extremum list
    // 3. Lido contract, during the report handling, calculates the value of finalization batchs in eth and shares
    //  and checks its correctness - `finalizationValue()`
    // 4. Lido contract finalize the requests pasing the required ether along with `finalize()` method

    struct CalcState {
        uint256 ethBudget;
        bool finished;
        uint256[] batches;
    }

    function calculateFinalizationBatches(uint256 _maxShareRate, uint256 _maxTimestamp, CalcState memory _state)
        external
        view
        returns (CalcState memory)
    {
        if (_state.finished) revert InvalidState();

        uint256 requestId;
        uint256 prevRequestShareRate;

        if (_state.batches.length == 0) {
            requestId = getLastFinalizedRequestId() + 1;
            // we'll store batches as a array where [MAX_REBASE_NUMBER] element is the array's length
            _state.batches = new uint256[](MAX_EXTREMA_PER_CALL + 1);
        } else {
            requestId = _state.batches[_state.batches[0]] + 1;
            prevRequestShareRate = _calcShareRate(_state.batches[_state.batches[0]], _maxShareRate);
        }

        uint256 lastRequestId = getLastRequestId();
        uint256 maxPossibleRequestId = requestId + MAX_REQUESTS_PER_CALL;

        uint256 extemumStartIndex = _getLastCheckedExtremum() + 1;
        uint256 extremaCounter;

        while (requestId < maxPossibleRequestId) {
            if (requestId > lastRequestId) break; // if end of the queue

            if (requestId == _getExtrema()[extemumStartIndex + extremaCounter]) {
                unchecked { ++extremaCounter; }
                if (extremaCounter > MAX_EXTREMA_PER_CALL) break;
            }

            WithdrawalRequest memory request = _getQueue()[requestId];

            if (request.timestamp > _maxTimestamp) break;

            WithdrawalRequest memory prevRequest = _getQueue()[requestId - 1];

            uint256 ethToFinalize = request.cumulativeStETH - prevRequest.cumulativeStETH;
            uint256 shareRequested = request.cumulativeShares - prevRequest.cumulativeShares;
            uint256 requestShareRate = ethToFinalize * E27_PRECISION_BASE / shareRequested;

            if (requestShareRate > _maxShareRate) {
                ethToFinalize = shareRequested * _maxShareRate / E27_PRECISION_BASE;
            }

            if (ethToFinalize > _state.ethBudget) break;

            _state.ethBudget -= ethToFinalize;

            if (_state.batches[MAX_EXTREMA_PER_CALL] != 0 && (
                prevRequest.reportTimestamp == request.reportTimestamp ||
                prevRequestShareRate <= _maxShareRate && requestShareRate <= _maxShareRate ||
                prevRequestShareRate > _maxShareRate && requestShareRate > _maxShareRate
            )) {
                _state.batches[_state.batches[MAX_EXTREMA_PER_CALL] - 1] = requestId;
            } else {
                _state.batches[_state.batches[MAX_EXTREMA_PER_CALL]] = requestId;
                ++_state.batches[MAX_EXTREMA_PER_CALL];
            }

            prevRequestShareRate = requestShareRate;
            unchecked{ ++requestId; }
        }

        _state.finished = requestId < maxPossibleRequestId || requestId == lastRequestId + 1;

        if (_state.finished) {
            assert(_state.batches[MAX_EXTREMA_PER_CALL] <= MAX_EXTREMA_PER_CALL);
            uint256[] memory batches = _state.batches;
            uint256 length = _state.batches[MAX_EXTREMA_PER_CALL];
            // todo: use MemUtils
            assembly {
                mstore(batches, length)
            }
        }

        return _state;
    }

    function onPreRebase(uint256 reportTimestamp) external {
        // TODO: auth and sanity checks
        _setLastReportTimestamp(reportTimestamp);
    }

    function prefinalize(uint256[] calldata _batches, uint256 _maxShareRate)
        public
        returns (uint256 ethToLock, uint256 sharesToBurn)
    {
        if (_maxShareRate == 0) revert ZeroShareRate();
        if (_batches.length == 0) revert EmptyBatches();

        uint256 lastIdInBatch = _batches[_batches.length - 1];
        if (lastIdInBatch > getLastRequestId()) revert InvalidRequestId(lastIdInBatch);

        uint256 firstIdInBatch = _batches[0];
        if (firstIdInBatch <= getLastFinalizedRequestId()) revert InvalidRequestId(firstIdInBatch);

        _setLastCheckedExtremum(_checkFinalizationBatchesIntegrity(_batches, _maxShareRate));

        uint256 preBatchStartId = getLastFinalizedRequestId();
        uint256 batchIndex;

        do {
            WithdrawalRequest memory batchStart = _getQueue()[preBatchStartId];
            WithdrawalRequest memory batchEnd = _getQueue()[_batches[batchIndex]];

            uint256 shares = batchEnd.cumulativeShares - batchStart.cumulativeShares;
            uint256 eth = batchEnd.cumulativeStETH - batchStart.cumulativeStETH;

            uint256 batchShareRate = (eth * E27_PRECISION_BASE) / shares;
            // todo: check equality
            if (batchShareRate > _maxShareRate) {
                ethToLock += shares * _maxShareRate / E27_PRECISION_BASE;
            } else {
                ethToLock += eth;
            }

            sharesToBurn += shares;

            preBatchStartId = _batches[batchIndex];
            unchecked{ ++batchIndex; }
        } while (batchIndex < _batches.length);
    }

    function _checkFinalizationBatchesIntegrity(uint256[] memory _batches, uint256 _maxShareRate)
        internal
        view
        returns (uint256 lastCheckedExtremum)
    {
        uint256 batchIndex = 0;
        uint256 batchPreStartId = getLastFinalizedRequestId();
        uint256 batchEndId = _batches[batchIndex];

        uint256 extremumIndex = _getLastCheckedExtremum();
        uint256 extremumLength = _getExtrema().length;
        uint256 extremumId = _getExtrema()[extremumIndex];

        uint256 batchShareRate= _calcShareRate(
                _getQueue()[batchPreStartId],
                _getQueue()[batchEndId],
                SHARE_RATE_UNLIMITED
            );

        while (batchIndex < _batches.length - 1) {
            if (extremumId <= batchEndId && extremumIndex < extremumLength - 1) {
                if (extremumId > batchPreStartId) {
                    // check extremum
                    uint256 extremumShareRate = _calcShareRate(extremumId, SHARE_RATE_UNLIMITED);

                    if (extremumShareRate > _maxShareRate && batchShareRate <= _maxShareRate) revert InvalidBatches();
                    if (extremumShareRate <= _maxShareRate && batchShareRate > _maxShareRate) revert InvalidBatches();
                }
                unchecked { ++extremumIndex; }
            } else {
                // check crossing point
                uint256 nextBatchShareRate = _calcShareRate(
                    _getQueue()[batchEndId],
                    _getQueue()[_batches[batchIndex + 1]],
                    SHARE_RATE_UNLIMITED
                );
                // avg batch rate before crossing point and after crossing point
                // can't be both below `_maxShareRate`
                if (batchShareRate <= _maxShareRate && nextBatchShareRate <= _maxShareRate) revert InvalidBatches();

                // avg batch rate before crossing point and after crossing point
                // can't be both above `_maxShareRate`
                if (batchShareRate > _maxShareRate && nextBatchShareRate > _maxShareRate) revert InvalidBatches();

                batchShareRate = nextBatchShareRate;
                batchPreStartId = batchEndId;
                unchecked { ++batchIndex; }
            }
        }

        return extremumIndex;
    }

    /// @dev Finalize requests from last finalized one up to `_nextFinalizedRequestId`
    ///  Emits WithdrawalBatchFinalized event.
    function _finalize(uint256[] memory _batches, uint256 _amountOfETH, uint256 _maxShareRate) internal {
        uint256 nextFinalizedRequestId = _batches[_batches.length - 1];
        if (nextFinalizedRequestId > getLastRequestId()) revert InvalidRequestId(nextFinalizedRequestId);
        uint256 lastFinalizedRequestId = getLastFinalizedRequestId();
        uint256 firstUnfinalizedRequestId = lastFinalizedRequestId + 1;
        if (nextFinalizedRequestId <= lastFinalizedRequestId) revert InvalidRequestId(nextFinalizedRequestId);

        WithdrawalRequest memory lastFinalizedRequest = _getQueue()[lastFinalizedRequestId];
        WithdrawalRequest memory requestToFinalize = _getQueue()[nextFinalizedRequestId];

        uint128 stETHToFinalize = requestToFinalize.cumulativeStETH - lastFinalizedRequest.cumulativeStETH;
        if (_amountOfETH > stETHToFinalize) revert TooMuchEtherToFinalize(_amountOfETH, stETHToFinalize);

        uint256 maxShareRate = SHARE_RATE_UNLIMITED;
        // if we have a crossing point or avg batch share rate is more than `_maxShareRate`
        if (_batches.length > 1 || stETHToFinalize > _amountOfETH) {
            maxShareRate = _maxShareRate;
        }

        uint256 lastCheckpointIndex = getLastCheckpointIndex();
        Checkpoint storage lastCheckpoint = _getCheckpoints()[lastCheckpointIndex];

        if (maxShareRate != lastCheckpoint.maxShareRate) {
            // add a new discount if it differs from the previous
            _getCheckpoints()[lastCheckpointIndex + 1] = Checkpoint(firstUnfinalizedRequestId, maxShareRate);
            _setLastCheckpointIndex(lastCheckpointIndex + 1);
        }

        _setLockedEtherAmount(getLockedEtherAmount() + _amountOfETH);
        _setLastFinalizedRequestId(nextFinalizedRequestId);

        emit WithdrawalBatchFinalized(
            firstUnfinalizedRequestId,
            nextFinalizedRequestId,
            _amountOfETH,
            requestToFinalize.cumulativeShares - lastFinalizedRequest.cumulativeShares,
            block.timestamp
            );
    }

    /// @dev creates a new `WithdrawalRequest` in the queue
    ///  Emits WithdrawalRequested event
    /// Does not check parameters
    function _enqueue(uint128 _amountOfStETH, uint128 _amountOfShares, address _owner)
        internal
        returns (uint256 requestId)
    {
        uint256 lastRequestId = getLastRequestId();
        WithdrawalRequest memory lastRequest = _getQueue()[lastRequestId];

        uint128 cumulativeShares = lastRequest.cumulativeShares + _amountOfShares;
        uint128 cumulativeStETH = lastRequest.cumulativeStETH + _amountOfStETH;

        requestId = lastRequestId + 1;

        _setLastRequestId(requestId);

        WithdrawalRequest memory newRequest =  WithdrawalRequest(
            cumulativeStETH,
            cumulativeShares,
            _owner,
            uint40(block.timestamp),
            false,
            uint40(_getLastReportTimestamp())
        );
        _getQueue()[requestId] = newRequest;
        assert(_getRequestsByOwner()[_owner].add(requestId));

        _populateExtrema(lastRequest, newRequest, requestId);

        emit WithdrawalRequested(requestId, msg.sender, _owner, _amountOfStETH, _amountOfShares);
    }

    /// @dev storing extrema of shareRate(requestId) function using three points:
    ///  newRequestId, prevRequestId and last known extremum id
    ///  - first request is always included as an extremum
    ///  - last request is not added by default to avoid storage write on each request
    ///     but speaking strictly last request is also an extremum
    ///  - if a lot of requests in a row have the same shareRate, the last one
    ///    will become an exremum as shareRate changes
    function _populateExtrema(
        WithdrawalRequest memory prevRequest,
        WithdrawalRequest memory newRequest,
        uint256 newRequestId
    ) internal {
        // shortcut for the same shareRate batches
        // requests is guaranteed to be the same shareRate if they belong to
        // the same oracle report period
        if (prevRequest.reportTimestamp == newRequest.reportTimestamp) return;

        uint256[] storage extrema = _getExtrema();
        // bootstrap the algo adding thee first request as an extrema by default
        if (extrema.length == 1 && newRequestId > 0) {
            extrema.push(newRequestId);
            return;
        }

        uint256 lastExtremumId = extrema[extrema.length - 1];
        WithdrawalRequest memory lastExtremumRequest = _getQueue()[lastExtremumId];

        uint256 newRequestShareRate = _calcShareRate(prevRequest, newRequest, SHARE_RATE_UNLIMITED);
        uint256 prevRequestShareRate = _calcShareRate(newRequestId - 1, SHARE_RATE_UNLIMITED);

        // we can get a new extremum only when shareRate changes
        // there can't be rounding jitter because we skipped on the same report requests in the beginning
        if (newRequestShareRate == prevRequestShareRate) return;

        uint256 lastExtremumShareRate = _calcShareRate(lastExtremumId, lastExtremumRequest);

        bool wasGrowing =  lastExtremumShareRate < prevRequestShareRate;
        // |  *
        // |•   •
        // +------->
        if (wasGrowing && prevRequestShareRate > newRequestShareRate) {
            extrema.push(newRequestId - 1);
            return;
        }
        //  |•   •
        //  |  *
        //  +------->
        if (!wasGrowing && prevRequestShareRate < newRequestShareRate) {
            extrema.push(newRequestId - 1);
            return;
        }
    }

    /// @notice Returns status of the withdrawal request with `_requestId` id
    function _getStatus(uint256 _requestId) internal view returns (WithdrawalRequestStatus memory status) {
        if (_requestId == 0 || _requestId > getLastRequestId()) revert InvalidRequestId(_requestId);

        WithdrawalRequest memory request = _getQueue()[_requestId];
        WithdrawalRequest memory previousRequest = _getQueue()[_requestId - 1];

        status = WithdrawalRequestStatus(
            request.cumulativeStETH - previousRequest.cumulativeStETH,
            request.cumulativeShares - previousRequest.cumulativeShares,
            request.owner,
            request.timestamp,
            _requestId <= getLastFinalizedRequestId(),
            request.claimed
        );
    }

    /// @notice View function to find a checkpoint hint for `claimWithdrawal()`
    ///  Search will be performed in the range of `[_firstIndex, _lastIndex]`
    ///
    /// NB!: Range search ought to be used to optimize gas cost.
    /// You can utilize the following invariant:
    /// `if (requestId2 > requestId1) than hint2 >= hint1`,
    /// so you can search for `hint2` in the range starting from `hint1`
    ///
    /// @param _requestId request id we are searching the checkpoint for
    /// @param _start index of the left boundary of the search range
    /// @param _end index of the right boundary of the search range
    ///
    /// @return value that hints `claimWithdrawal` to find the discount for the request,
    ///  or 0 if hint not found in the range
    function _findCheckpointHint(uint256 _requestId, uint256 _start, uint256 _end) internal view returns (uint256) {
        if (_requestId == 0) revert InvalidRequestId(_requestId);
        if (_start == 0) revert InvalidRequestIdRange(_start, _end);
        uint256 lastCheckpointIndex = getLastCheckpointIndex();
        if (_end > lastCheckpointIndex) revert InvalidRequestIdRange(_start, _end);
        if (_requestId > getLastFinalizedRequestId()) revert RequestNotFoundOrNotFinalized(_requestId);

        if (_start > _end) return NOT_FOUND; // we have an empty range to search in, so return NOT_FOUND

        // Right boundary
        if (_requestId >= _getCheckpoints()[_end].fromRequestId) {
            // it's the last checkpoint, so it's valid
            if (_end == lastCheckpointIndex) return _end;
            // it fits right before the next checkpoint
            if (_requestId < _getCheckpoints()[_end + 1].fromRequestId) return _end;

            return NOT_FOUND;
        }
        // Left boundary
        if (_requestId < _getCheckpoints()[_start].fromRequestId) {
            return NOT_FOUND;
        }

        // Binary search
        uint256 min = _start;
        uint256 max = _end - 1;

        while (max > min) {
            uint256 mid = (max + min + 1) / 2;
            if (_getCheckpoints()[mid].fromRequestId <= _requestId) {
                min = mid;
            } else {
                max = mid - 1;
            }
        }
        return min;
    }

    /// @notice Claim `_requestId` request and transfer locked ether to `_recipient`. Emits WithdrawalClaimed event
    /// @param _requestId request id to claim
    /// @param _hint hint for discount checkpoint index to avoid extensive search over the checkpoints.
    /// @param _recipient address to send ether to
    function _claim(uint256 _requestId, uint256 _hint, address _recipient) internal {
        if (_requestId == 0) revert InvalidRequestId(_requestId);
        if (_requestId > getLastFinalizedRequestId()) revert RequestNotFoundOrNotFinalized(_requestId);

        WithdrawalRequest storage request = _getQueue()[_requestId];

        if (request.claimed) revert RequestAlreadyClaimed(_requestId);
        if (request.owner != msg.sender) revert NotOwner(msg.sender, request.owner);

        request.claimed = true;
        assert(_getRequestsByOwner()[request.owner].remove(_requestId));

        uint256 ethWithDiscount = _calculateClaimableEther(request, _requestId, _hint);

        _setLockedEtherAmount(getLockedEtherAmount() - ethWithDiscount);
        _sendValue(payable(_recipient), ethWithDiscount);

        emit WithdrawalClaimed(_requestId, msg.sender, _recipient, ethWithDiscount);
    }

    /// @notice Calculates discounted ether value for `_requestId` using a provided `_hint`. Checks if hint is valid
    /// @return claimableEther discounted eth for `_requestId`. Returns 0 if request is not claimable
    function _calculateClaimableEther(WithdrawalRequest storage _request, uint256 _requestId, uint256 _hint)
        internal
        view
        returns (uint256 claimableEther)
    {
        if (_hint == 0) revert InvalidHint(_hint);

        uint256 lastCheckpointIndex = getLastCheckpointIndex();
        if (_hint > lastCheckpointIndex) revert InvalidHint(_hint);

        Checkpoint memory checkpoint = _getCheckpoints()[_hint];
        // ______(>______
        //    ^  hint
        if (_requestId < checkpoint.fromRequestId) revert InvalidHint(_hint);
        if (_hint < lastCheckpointIndex) {
            // ______(>______(>________
            //       hint    hint+1  ^
            Checkpoint memory nextCheckpoint = _getCheckpoints()[_hint + 1];
            if (nextCheckpoint.fromRequestId <= _requestId) {
                revert InvalidHint(_hint);
            }
        }

        WithdrawalRequest memory prevRequest = _getQueue()[_requestId - 1];

        uint256 ethRequested = _request.cumulativeStETH - prevRequest.cumulativeStETH;
        uint256 shareRequested = _request.cumulativeShares - prevRequest.cumulativeShares;

        if (ethRequested * E27_PRECISION_BASE / shareRequested <= checkpoint.maxShareRate) {
            return ethRequested;
        }

        return shareRequested * checkpoint.maxShareRate / E27_PRECISION_BASE;
    }

    // quazi-constructor
    function _initializeQueue() internal {
        // setting dummy zero structs in checkpoints and queue beginning
        // to avoid uint underflows and related if-branches
        // 0-index is reserved as 'not_found' response in the interface everywhere
        _getQueue()[0] = WithdrawalRequest(0, 0, address(0), uint40(block.timestamp), true, 0);
        _getCheckpoints()[getLastCheckpointIndex()] = Checkpoint(0, 0);
        _getExtrema().push(0);
    }

    function _sendValue(address _recipient, uint256 _amount) internal {
        if (address(this).balance < _amount) revert NotEnoughEther();

        // solhint-disable-next-line
        (bool success,) = _recipient.call{value: _amount}("");
        if (!success) revert CantSendValueRecipientMayHaveReverted();
    }

    /// calculate avg share rate for the batch of (_preStartRequest, _endRequest]
    function _calcShareRate(
        WithdrawalRequest memory _preStartRequest,
        WithdrawalRequest memory _endRequest,
        uint256 _maxShareRate
    ) internal pure returns (uint256 shareRate) {
        uint256 ethRequested = _endRequest.cumulativeStETH - _preStartRequest.cumulativeStETH;
        uint256 shareRequested = _endRequest.cumulativeShares - _preStartRequest.cumulativeShares;

        return Math.min(ethRequested * E27_PRECISION_BASE / shareRequested, _maxShareRate);
    }

    function _calcShareRate(uint256 _requestId, uint256 _maxShareRate) internal view returns (uint256) {
        WithdrawalRequest memory prevRequest = _getQueue()[_requestId - 1];
        WithdrawalRequest memory lastRequest = _getQueue()[_requestId];

        return _calcShareRate(prevRequest, lastRequest, _maxShareRate);
    }

    function _calcShareRate(uint256 _requestId, WithdrawalRequest memory request)
        internal
        view
        returns (uint256)
    {
        WithdrawalRequest memory prevRequest = _getQueue()[_requestId - 1];

        return _calcShareRate(prevRequest, request, SHARE_RATE_UNLIMITED);
    }

    //
    // Internal getters and setters
    //
    function _getQueue() internal pure returns (mapping(uint256 => WithdrawalRequest) storage queue) {
        bytes32 position = QUEUE_POSITION;
        assembly {
            queue.slot := position
        }
    }

    function _getCheckpoints() internal pure returns (mapping(uint256 => Checkpoint) storage checkpoints) {
        bytes32 position = CHECKPOINTS_POSITION;
        assembly {
            checkpoints.slot := position
        }
    }

    function _getRequestsByOwner()
        internal
        pure
        returns (mapping(address => EnumerableSet.UintSet) storage requestsByOwner)
    {
        bytes32 position = REQUEST_BY_OWNER_POSITION;
        assembly {
            requestsByOwner.slot := position
        }
    }

    function _getExtrema() internal pure returns (uint256[] storage) {
        return EXTREMA_POSITION.storageUint256Array();
    }

    function _getLastCheckedExtremum() internal view returns (uint256) {
        return LAST_CHECKED_EXTREMUM_POSITION.getStorageUint256();
    }

    function _getLastReportTimestamp() internal view returns (uint256) {
        return LAST_REPORT_TIMESTAMP_POSITION.getStorageUint256();
    }

    function _setLastRequestId(uint256 _lastRequestId) internal {
        LAST_REQUEST_ID_POSITION.setStorageUint256(_lastRequestId);
    }

    function _setLastFinalizedRequestId(uint256 _lastFinalizedRequestId) internal {
        LAST_FINALIZED_REQUEST_ID_POSITION.setStorageUint256(_lastFinalizedRequestId);
    }

    function _setLastCheckpointIndex(uint256 _lastCheckpointIndex) internal {
        LAST_CHECKPOINT_INDEX_POSITION.setStorageUint256(_lastCheckpointIndex);
    }

    function _setLockedEtherAmount(uint256 _lockedEtherAmount) internal {
        LOCKED_ETHER_AMOUNT_POSITION.setStorageUint256(_lockedEtherAmount);
    }

    function _setLastCheckedExtremum(uint256 _lastCheckedExtremum) internal {
        LAST_CHECKED_EXTREMUM_POSITION.setStorageUint256(_lastCheckedExtremum);
    }

    function _setLastReportTimestamp(uint256 _lastReportTimestamp) internal {
        LAST_REPORT_TIMESTAMP_POSITION.setStorageUint256(_lastReportTimestamp);
    }
}
