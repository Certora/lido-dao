// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import "../../contracts/0.8.9/WithdrawalQueue.sol";

contract WithdrawalQueueHarness is WithdrawalQueue {

    constructor(IWstETH _wstETH)WithdrawalQueue(_wstETH) {}

    function getRequestsStatusAmountOfStETH(uint256 requestId) public returns (uint256) {
        WithdrawalRequestStatus memory req = getWithdrawalRequestStatus(requestId);
        return req.amountOfStETH;
    }

    function getRequestsStatusAmountOfShares(uint256 requestId) public returns (uint256) {
        WithdrawalRequestStatus memory req = getWithdrawalRequestStatus(requestId);
        return req.amountOfShares;
    }

    function getRequestsStatusOwner(uint256 requestId) public returns (address) {
        WithdrawalRequestStatus memory req = getWithdrawalRequestStatus(requestId);
        return req.owner;
    }

    function isRequestStatusClaimed(uint256 requestId) public returns (bool) {
        WithdrawalRequestStatus memory req = getWithdrawalRequestStatus(requestId);
        return req.isClaimed;
    }

    function isRequestStatusFinalized(uint256 requestId) public returns (bool) {
        WithdrawalRequestStatus memory req = getWithdrawalRequestStatus(requestId);
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

    function claimWithdrawalHarness(uint256 requestId, uint256 hint) public {
        ClaimWithdrawalInput[] memory claimWithdrawalInputs;
        ClaimWithdrawalInput memory input = ClaimWithdrawalInput(requestId, hint);
        claimWithdrawalInputs[0] = input;
        this.claimWithdrawals(claimWithdrawalInputs);
    }   

    function _emitTransfer(address from, address to, uint256 _requestId) internal override {}

}
