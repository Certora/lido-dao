// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

contract withdrawalQueueMock {

    uint256 public lockedEth;
    mapping(uint256 => uint256) public cumulativeStEthbyId;
    uint256 public getLastRequestId;
    uint256 public getLastFinalizedRequestId;

    function finalize(uint256[] calldata _batches, uint256 _maxShareRate)
        external
        payable
    {
        _finalize(msg.value, _maxShareRate);
    }

    function _finalize(uint256 _amountOfETH, uint256 _maxShareRate) internal {
        lockedEth = lockedEth + _amountOfETH;
    } 

    function unfinalizedStETH() external view returns (uint256) {
        return
            cumulativeStEthbyId[getLastRequestId] - cumulativeStEthbyId[getLastFinalizedRequestId];
    }


    // function prefinalize(uint256[] _batches, uint256 _maxShareRate)
    //     external
    //     view
    //     returns (uint256 ethToLock, uint256 sharesToBurn);

    // function finalize(uint256[] _batches, uint256 _maxShareRate) external payable;

    // function isPaused() external view returns (bool);

    // function unfinalizedStETH() external view returns (uint256);

    // function isBunkerModeActive() external view returns (bool);

}
