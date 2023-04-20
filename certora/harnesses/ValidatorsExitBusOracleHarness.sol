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

    function submitReportDataHelper(uint256 consensusVersion, uint256 refSlot, uint256 requestsCount, uint256 dataFormat, bytes calldata dataInput, uint256 contractVersion)
        external
    {
        ReportData memory data = ReportData({
            consensusVersion: consensusVersion,
            refSlot: refSlot,
            requestsCount: requestsCount,
            dataFormat: dataFormat,
            data: dataInput
        });
        submitReportData(data, contractVersion);
    }

    function matchReportDatas(uint256 consensusVersion, uint256 refSlot, uint256 requestsCount, uint256 dataFormat, bytes calldata dataInput) public view returns (bool) {
        return dataGlobal.consensusVersion == consensusVersion &&
            dataGlobal.refSlot == refSlot &&
            dataGlobal.requestsCount == requestsCount &&
            dataGlobal.dataFormat == dataFormat &&
            compareBytes(dataGlobal.data, dataInput);
    }

    function compareBytes(bytes memory a, bytes memory b) public pure returns (bool) {
        return keccak256(abi.encodePacked(a)) == keccak256(abi.encodePacked(b));
    }

    function getConsensusVersionGlobal() public view returns (uint256) {
        return dataGlobal.consensusVersion;
    }

    function getRefSlotGlobal() public view returns (uint256) {
        return dataGlobal.refSlot;
    }

    function getRequestsCountGlobal() public view returns (uint256) {
        return dataGlobal.requestsCount;
    }

    function getDataFormatGlobal() public view returns (uint256) {
        return dataGlobal.dataFormat;
    }

    function getDataGlobal() public view returns (bytes memory) {
        return dataGlobal.data;
    }

    function callGetLastRequestedValidatorIndices(uint256 moduleId, uint256[] calldata nodeOpIds, uint256 index)
        external view returns (int256)
    {
        int256[] memory indices = getLastRequestedValidatorIndices(moduleId, nodeOpIds);
        return indices.length <= index ? int256(0) : indices[index];
    }

    function isConsensusMember(address addr) public view returns (bool) {
        return _isConsensusMember(addr);
    }

    function checkContractVersion(uint256 version) public view {
        _checkContractVersion(version);
    }

    function getRefSlot() public view returns (uint256) {
        return _storageConsensusReport().value.refSlot;
    }

    function getReportHash() public view returns (bytes32) {
        return _storageConsensusReport().value.hash;
    }
}
