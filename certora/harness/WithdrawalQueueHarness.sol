// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import "../../contracts/0.8.9/WithdrawalQueue.sol";

contract WithdrawalQueueHarness is WithdrawalQueue {

    constructor(IWstETH _wstETH)WithdrawalQueue(_wstETH) {}

    function getRequestsStatusAmountOfStETH(uint256 requestId) public returns (uint256) {
        WithdrawalRequestStatus memory req = _getStatus(requestId);
        return req.amountOfStETH;
    }

    function getRequestsStatusAmountOfShares(uint256 requestId) public returns (uint256) {
        WithdrawalRequestStatus memory req = _getStatus(requestId);
        return req.amountOfShares;
    }

    function getRequestsStatusOwner(uint256 requestId) public returns (address) {
        WithdrawalRequestStatus memory req = _getStatus(requestId);
        return req.owner;
    }

    function isRequestStatusClaimed(uint256 requestId) public returns (bool) {
        WithdrawalRequestStatus memory req = _getStatus(requestId);
        return req.isClaimed;
    }

    function isRequestStatusFinalized(uint256 requestId) public returns (bool) {
        WithdrawalRequestStatus memory req = _getStatus(requestId);
        return req.isFinalized;
    }

    // function calculateFinalizationParamsForReqId(
    //     uint256 _lastIdToFinalize,
    //     uint256 _totalPooledEther,
    //     uint256 _totalShares
    // ) public view returns (uint256 etherToLock, uint256 sharesToBurn) {
    //     return _calculateDiscountedBatch(
    //         _lastIdToFinalize,
    //         _lastIdToFinalize,
    //         _toUint128(_totalPooledEther),
    //         _toUint128(_totalShares)
    //     );
    // }

    // function isPriceHintValid(uint256 _requestId, uint256 hint) public view returns (bool isInRange) {
    //     return _isPriceHintValid(_requestId, hint);
    // }

    function balanceOfEth(address user) public view returns(uint256)
    {
        return user.balance;
    }

    // function claimWithdrawalHarness(uint256 requestId, uint256 hint) public {
    //     ClaimWithdrawalInput[] memory claimWithdrawalInputs;
    //     ClaimWithdrawalInput memory input = ClaimWithdrawalInput(requestId, hint);
    //     claimWithdrawalInputs[0] = input;
    //     this.claimWithdrawals(claimWithdrawalInputs);
    // }   
    function getRequestCumulativeStEth(uint256 requestId) public view returns(uint256) {
        WithdrawalRequest memory request = _getQueue()[requestId];

        return request.cumulativeStETH;
    }

    function getRequestCumulativeShares(uint256 requestId) public view returns(uint256) {
        WithdrawalRequest memory request = _getQueue()[requestId];

        return request.cumulativeShares;
    }

    function _emitTransfer(address from, address to, uint256 _requestId) internal override {}

    function requestWithdrawal(uint256 amount, address _owner) public returns (uint256) {
        _checkWithdrawalRequestAmount(amount);
        return _requestWithdrawal(amount, _owner);
    }

    function claimWithdrawal(uint256 requestId, uint256 hintIndex) public {
        _claim(requestId,hintIndex, msg.sender);
    }

    function getDiscountFactorByIndex(uint256 checkpointIndex) public returns (uint256) {
        DiscountCheckpoint storage lastCheckpoint = _getCheckpoints()[checkpointIndex];
        return lastCheckpoint.discountFactor;
    }
}
