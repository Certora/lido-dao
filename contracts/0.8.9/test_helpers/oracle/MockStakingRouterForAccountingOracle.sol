// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import { IStakingRouter } from "../../oracle/AccountingOracle.sol";


contract MockStakingRouterForAccountingOracle is IStakingRouter {

    struct UpdateExitedKeysByModuleCallData {
        uint256[] moduleIds;
        uint256[] exitedKeysCounts;
        uint256 callCount;
    }

    struct ReportKeysByNodeOperatorCallData {
        uint256 stakingModuleId;
        bytes nodeOperatorIds;
        bytes keysCounts;
    }

    uint256 internal _exitedKeysCountAcrossAllModules;
    UpdateExitedKeysByModuleCallData internal _lastCall_updateExitedKeysByModule;

    ReportKeysByNodeOperatorCallData[] public calls_reportExitedKeysByNodeOperator;
    ReportKeysByNodeOperatorCallData[] public calls_reportStuckKeysByNodeOperator;


    function setExitedKeysCountAcrossAllModules(uint256 count) external {
        _exitedKeysCountAcrossAllModules = count;
    }

    function lastCall_updateExitedKeysByModule()
        external view returns (UpdateExitedKeysByModuleCallData memory)
    {
        return _lastCall_updateExitedKeysByModule;
    }

    function totalCalls_reportExitedKeysByNodeOperator() external view returns (uint256) {
        return calls_reportExitedKeysByNodeOperator.length;
    }

    function totalCalls_reportStuckKeysByNodeOperator() external view returns (uint256) {
        return calls_reportStuckKeysByNodeOperator.length;
    }

    ///
    /// IStakingRouter
    ///

    function getExitedValidatorsCountAcrossAllModules() external view returns (uint256) {
        return _exitedKeysCountAcrossAllModules;
    }

    function updateExitedValidatorsCountByStakingModule(
        uint256[] calldata moduleIds,
        uint256[] calldata exitedKeysCounts
    ) external {
        _lastCall_updateExitedKeysByModule.moduleIds = moduleIds;
        _lastCall_updateExitedKeysByModule.exitedKeysCounts = exitedKeysCounts;
        ++_lastCall_updateExitedKeysByModule.callCount;
    }

    function reportStakingModuleExitedValidatorsCountByNodeOperator(
        uint256 stakingModuleId,
        bytes calldata nodeOperatorIds,
        bytes calldata exitedKeysCounts
    ) external {
        calls_reportExitedKeysByNodeOperator.push(ReportKeysByNodeOperatorCallData(
            stakingModuleId, nodeOperatorIds, exitedKeysCounts
        ));
    }

    function reportStakingModuleStuckValidatorsCountByNodeOperator(
        uint256 stakingModuleId,
        bytes calldata nodeOperatorIds,
        bytes calldata stuckKeysCounts
    ) external {
        calls_reportStuckKeysByNodeOperator.push(ReportKeysByNodeOperatorCallData(
            stakingModuleId, nodeOperatorIds, stuckKeysCounts
        ));
    }
}
