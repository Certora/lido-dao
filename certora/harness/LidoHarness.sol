// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.4.24;

import "../../contracts/0.4.24/Lido.sol";

contract LidoHarness is Lido {
    /// @notice Certora : use storage variables as direct arguments for the handleReport steps
    OracleReportContracts private contracts;
    OracleReportedData private reportedData;
    OracleReportContext private reportContext;

    function getIsStopped() public view returns (bool) {
        return isStopped();
    }

    function processClStateUpdate(uint256 _reportTimestamp, uint256 _preClValidators, uint256 _postClValidators, uint256 _postClBalance) public returns (uint256) {
        _requireReportValidTimeStamp();
        return _processClStateUpdate(_reportTimestamp, _preClValidators, _postClValidators, _postClBalance);
    }

    function collectRewardsAndProcessWithdrawals(
        uint256 _withdrawalsToWithdraw,
        uint256 _elRewardsToWithdraw,
        uint256[] _withdrawalFinalizationBatches,
        uint256 _simulatedShareRate,
        uint256 _etherToLockOnWithdrawalQueue
    ) public {
        _requireReportValidTimeStamp();
        _collectRewardsAndProcessWithdrawals(contracts, _withdrawalsToWithdraw, _elRewardsToWithdraw, _withdrawalFinalizationBatches, _simulatedShareRate, _etherToLockOnWithdrawalQueue);
    }

    function calculateWithdrawals() public view returns (uint256, uint256) {
        return _calculateWithdrawals(contracts, reportedData);
    }

    function processRewards(
        uint256 _postCLBalance,
        uint256 _withdrawnWithdrawals,
        uint256 _withdrawnElRewards
    ) public returns (uint256) {
        _requireReportValidTimeStamp();
        return _processRewards(reportContext, _postCLBalance, _withdrawnWithdrawals, _withdrawnElRewards);
    }

    function distributeFee(
        uint256 _preTotalPooledEther,
        uint256 _preTotalShares,
        uint256 _totalRewards
    ) public returns (uint256) {
        _requireReportValidTimeStamp();
        return _distributeFee(_preTotalPooledEther, _preTotalShares, _totalRewards);
    }

    function transferModuleRewards(
        address[] memory recipients,
        uint96[] memory modulesFees,
        uint256 totalFee,
        uint256 totalRewards
    ) public returns (uint256[] memory moduleRewards, uint256 totalModuleRewards) {
        return _transferModuleRewards(recipients, modulesFees, totalFee, totalRewards);
    }

    function transferTreasuryRewards(uint256 treasuryReward) public {
        return _transferTreasuryRewards(treasuryReward);
    }

    function getTransientBalance() public view returns (uint256) {
        return _getTransientBalance();
    }

    function completeTokenRebase(
        address _postTokenRebaseReceiver
    ) public returns (uint256, uint256) {
        return _completeTokenRebase(reportedData, reportContext, 
            IPostTokenRebaseReceiver(_postTokenRebaseReceiver));
    }

    function setOracleReportContracts() public {
        contracts = _loadOracleReportContracts();
    }

    // function handleOracleReportWrapper(
    //     // Oracle timings
    //     uint256 _reportTimestamp,
    //     uint256 _timeElapsed,
    //     // CL values
    //     uint256 _clValidators,
    //     uint256 _clBalance,
    //     // EL values
    //     uint256 _withdrawalVaultBalance,
    //     uint256 _elRewardsVaultBalance,
    //     uint256 _sharesRequestedToBurn,
    //     // Decision about withdrawals processing
    //     uint256 _withdrawalFinalizationBatch,
    //     uint256 _simulatedShareRate) public returns (uint256 a, uint256 b, uint256 c, uint256 d) {

    //     uint256[] memory _withdrawalFinalizationBatches = new uint256[](1);
    //     _withdrawalFinalizationBatches[0] = _withdrawalFinalizationBatch;

    //     uint256[4] memory postRebaseAmounts; // = new uint256[](4);
        
    //     // postRebaseAmounts = handleOracleReport(_reportTimestamp, _timeElapsed, _clValidators, _clBalance, _withdrawalVaultBalance, _elRewardsVaultBalance, _sharesRequestedToBurn, _withdrawalFinalizationBatches, _simulatedShareRate);
    //     postRebaseAmounts = _handleOracleReport(
    //         OracleReportedData( 
    //             _reportTimestamp,
    //             _timeElapsed,
    //             _clValidators,
    //             _clBalance,
    //             _withdrawalVaultBalance,
    //             _elRewardsVaultBalance,
    //             _sharesRequestedToBurn,
    //             _withdrawalFinalizationBatches,
    //             _simulatedShareRate
    //         )
    //     );
    //     return (postRebaseAmounts[0], postRebaseAmounts[1], postRebaseAmounts[2], postRebaseAmounts[3]);
    // }

    function stakingModuleMaxDepositsCount(uint256 _stakingModuleId, uint256 _maxValue) public view returns (uint256) {
        IStakingRouter stakingRouter = IStakingRouter(getLidoLocator().stakingRouter());
        return stakingRouter.getStakingModuleMaxDepositsCount(_stakingModuleId, _maxValue);
    }

    function LidoEthBalance() public view returns(uint256) {
        return address(this).balance;
    }

    function getEthBalance(address account) public view returns(uint256) {
        return account.balance;
    }

    function _requireReportValidTimeStamp() internal view {
        require(reportedData.reportTimestamp <= block.timestamp, "INVALID_REPORT_TIMESTAMP");
    }
}