// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import { ILido } from "../../oracle/AccountingOracle.sol";


contract MockLidoForAccountingOracle is ILido {

    struct HandleOracleReportLastCall {
        uint256 currentReportTimestamp;
        uint256 secondsElapsedSinceLastReport;
        uint256 numValidators;
        uint256 clBalance;
        uint256 withdrawalVaultBalance;
        uint256 elRewardsVaultBalance;
        uint256 lastWithdrawalRequestIdToFinalize;
        uint256 finalizationShareRate;
        uint256 callCount;
    }

    HandleOracleReportLastCall internal _handleOracleReportLastCall;

    function getLastCall_handleOracleReport() external view returns (HandleOracleReportLastCall memory) {
        return _handleOracleReportLastCall;
    }

    ///
    /// ILido
    ///

    function handleOracleReport(
        uint256 currentReportTimestamp,
        uint256 secondsElapsedSinceLastReport,
        uint256 numValidators,
        uint256 clBalance,
        uint256 withdrawalVaultBalance,
        uint256 elRewardsVaultBalance,
        uint256 lastWithdrawalRequestIdToFinalize,
        uint256 finalizationShareRate
    ) external {
        _handleOracleReportLastCall.currentReportTimestamp = currentReportTimestamp;
        _handleOracleReportLastCall.secondsElapsedSinceLastReport = secondsElapsedSinceLastReport;
        _handleOracleReportLastCall.numValidators = numValidators;
        _handleOracleReportLastCall.clBalance = clBalance;
        _handleOracleReportLastCall.withdrawalVaultBalance = withdrawalVaultBalance;
        _handleOracleReportLastCall.elRewardsVaultBalance = elRewardsVaultBalance;
        _handleOracleReportLastCall.lastWithdrawalRequestIdToFinalize = lastWithdrawalRequestIdToFinalize;
        _handleOracleReportLastCall.finalizationShareRate = finalizationShareRate;
        ++_handleOracleReportLastCall.callCount;
    }
}
