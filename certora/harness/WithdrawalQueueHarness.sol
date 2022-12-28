// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import "../../contracts/0.8.9/WithdrawalQueue.sol";

contract WithdrawalQueueHarness is WithdrawalQueue {

    constructor(address payable _owner)WithdrawalQueue(_owner) {}
    function getRequestById(uint256 requestId) internal returns (Request memory) {
        return queue[requestId];
    }

    function getRequestsCumulativeEther(uint256 requestId) public returns (uint128) {
        Request memory req = getRequestById(requestId);
        return req.cumulativeEther;
    }

    function getRequestsCumulativeShares(uint256 requestId) public returns (uint128) {
        Request memory req = getRequestById(requestId);
        return req.cumulativeShares;
    }

    function getRequestsRecipient(uint256 requestId) public returns (address) {
        Request memory req = getRequestById(requestId);
        return req.recipient;
    }

    function isRequestClaimed(uint256 requestId) public returns (bool) {
        Request memory req = getRequestById(requestId);
        return req.claimed;
    }

}
