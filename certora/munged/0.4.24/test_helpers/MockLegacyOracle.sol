// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.4.24;

import "../oracle/LegacyOracle.sol";

interface ILegacyOracle {
    function getBeaconSpec() external view returns (
        uint64 epochsPerFrame,
        uint64 slotsPerEpoch,
        uint64 secondsPerSlot,
        uint64 genesisTime
    );

    function getLastCompletedEpochId() external view returns (uint256);
}

interface ITimeProvider {
    function getTime() external view returns (uint256);
}


contract MockLegacyOracle is ILegacyOracle, LegacyOracle {

    struct HandleConsensusLayerReportCallData {
        uint256 totalCalls;
        uint256 refSlot;
        uint256 clBalance;
        uint256 clValidators;
    }

    HandleConsensusLayerReportCallData public lastCall__handleConsensusLayerReport;


    function getBeaconSpec() external view returns (
        uint64 epochsPerFrame,
        uint64 slotsPerEpoch,
        uint64 secondsPerSlot,
        uint64 genesisTime
    ) {

        ChainSpec memory spec =  _getChainSpec();
        epochsPerFrame = spec.epochsPerFrame;
        slotsPerEpoch = spec.slotsPerEpoch;
        secondsPerSlot = spec.secondsPerSlot;
        genesisTime = spec.genesisTime;
    }

    function setBeaconSpec( uint64 epochsPerFrame,
        uint64 slotsPerEpoch,
        uint64 secondsPerSlot,
        uint64 genesisTime) external {
            _setChainSpec(ChainSpec(epochsPerFrame,slotsPerEpoch,secondsPerSlot,genesisTime));
    }

    
     function _getTime() internal view returns (uint256) {
        address accountingOracle = ACCOUNTING_ORACLE_POSITION.getStorageAddress();
        return ITimeProvider(accountingOracle).getTime();
    }

     function getTime() external view returns (uint256) {
        return _getTime();
    }

   

    function handleConsensusLayerReport(uint256 refSlot, uint256 clBalance, uint256 clValidators)
        external
    {
        ++lastCall__handleConsensusLayerReport.totalCalls;
        lastCall__handleConsensusLayerReport.refSlot = refSlot;
        lastCall__handleConsensusLayerReport.clBalance = clBalance;
        lastCall__handleConsensusLayerReport.clValidators = clValidators;
    }


    function setParams(
        uint64 epochsPerFrame,
        uint64 slotsPerEpoch,
        uint64 secondsPerSlot,
        uint64 genesisTime,
        uint256 lastCompletedEpochId
    ) external {
          _setChainSpec(ChainSpec(epochsPerFrame,slotsPerEpoch,secondsPerSlot,genesisTime));
        LAST_COMPLETED_EPOCH_ID_POSITION.setStorageUint256(lastCompletedEpochId);
    }
 
    function setLastCompletedEpochId(uint256 lastCompletedEpochId) external {
         LAST_COMPLETED_EPOCH_ID_POSITION.setStorageUint256(lastCompletedEpochId);
    }

    function initializeAsV3() external {
        CONTRACT_VERSION_POSITION_DEPRECATED.setStorageUint256(3);
    }

}
