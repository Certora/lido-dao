// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>

// SPDX-License-Identifier: GPL-3.0

pragma solidity 0.4.24;

import "openzeppelin-solidity/contracts/introspection/ERC165.sol";


contract BeaconReportReceiverMock is ERC165 {
    uint256 public postTotalPooledEther;
    uint256 public preTotalPooledEther;
    uint256 public timeElapsed;
    uint256 public gas;

    constructor() public {
        BeaconReportReceiverMock iBeacon;
        _registerInterface(iBeacon.processLidoOracleReport.selector);
    }

    function processLidoOracleReport(uint256 _postTotalPooledEther,
                                     uint256 _preTotalPooledEther,
                                     uint256 _timeElapsed) external {
        gas = gasleft();
        postTotalPooledEther = _postTotalPooledEther;
        preTotalPooledEther = _preTotalPooledEther;
        timeElapsed = _timeElapsed;
    }
}

contract BeaconReportReceiverMockWithoutERC165 {
    function processLidoOracleReport(
        uint256 /* _postTotalPooledEther */,
        uint256 /* _preTotalPooledEther */,
        uint256 /* _timeElapsed */
    ) external
    { }
}
