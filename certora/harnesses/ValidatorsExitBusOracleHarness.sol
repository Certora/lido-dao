// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import "../munged/0.8.9/oracle/ValidatorsExitBusOracle.sol";


contract ValidatorsExitBusOracleHarness is ValidatorsExitBusOracle {

    constructor(uint256 secondsPerSlot, uint256 genesisTime, address lidoLocator)
        ValidatorsExitBusOracle(secondsPerSlot, genesisTime, lidoLocator)
    { }

    function getMaxValidatorExitRequestsPerReport() public view returns (uint256) {
        return IOracleReportSanityChecker(LOCATOR.oracleReportSanityChecker()).getOracleReportLimits().maxValidatorExitRequestsPerReport;
    }

    function submitReportDataHelper(ReportData calldata data, uint256 consensusVersion, uint256 refSlot, uint256 requestsCount, uint256 dataFormat, bytes calldata dataInput, uint256 contractVersion)
        external
    {
        require(data.consensusVersion == consensusVersion);
        require(data.refSlot == refSlot);
        require(data.requestsCount == requestsCount);
        require(data.dataFormat == dataFormat);
        require(keccak256(abi.encodePacked(data.data)) == keccak256(abi.encodePacked(dataInput)));
        submitReportData(data, contractVersion);
    }

    function compareBytes(bytes memory a, bytes memory b) public pure returns (bool) {
        return keccak256(abi.encodePacked(a)) == keccak256(abi.encodePacked(b));
    }
}
