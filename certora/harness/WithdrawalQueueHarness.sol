// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import "../../contracts/0.8.9/WithdrawalQueue.sol";

contract WithdrawalQueueHarness is WithdrawalQueue {

    constructor(address payable _owner)WithdrawalQueue(_owner) {}
    function getRequestById(uint256 requestId) internal returns (Request storage) {
        return queue[requestId];
    }

    function getPricesLength() public view returns (uint256) {
        return finalizationPrices.length;
    }

    function getRequestsCumulativeEther(uint256 requestId) public returns (uint128) {
        Request storage req = getRequestById(requestId);
        return req.cumulativeEther;
    }

    function getRequestsCumulativeShares(uint256 requestId) public returns (uint128) {
        Request storage req = getRequestById(requestId);
        return req.cumulativeShares;
    }

    function getRequestsRecipient(uint256 requestId) public returns (address) {
        Request storage req = getRequestById(requestId);
        return req.recipient;
    }

    function isRequestClaimed(uint256 requestId) public returns (bool) {
        Request storage req = getRequestById(requestId);
        return req.claimed;
    }

    function calculateFinalizationParamsForReqId(
        uint256 _lastIdToFinalize,
        uint256 _totalPooledEther,
        uint256 _totalShares
    ) public view returns (uint256 etherToLock, uint256 sharesToBurn) {
        return _calculateDiscountedBatch(
            _lastIdToFinalize,
            _lastIdToFinalize,
            _toUint128(_totalPooledEther),
            _toUint128(_totalShares)
        );
    }

    function isPriceHintValid(uint256 _requestId, uint256 hint) public view returns (bool isInRange) {
        return _isPriceHintValid(_requestId, hint);
    }

    function balnceOfEth(address user) public view returns(uint256)
    {
        return user.balance;
    }

    function getFinalizationPricesLength() public returns (uint256) {
        return finalizationPrices.length;
    }

    function getPriceIndex(uint256 priceIndex) public returns (uint256) {
        return finalizationPrices[priceIndex].index;
    }

}
