pragma solidity 0.4.24;

import "../../contracts/0.4.24/Lido.sol";

contract LidoHarness is Lido {
    function getIsStopped() public view returns (bool) {
        return isStopped();
    }

    function processClStateUpdate(uint256 _reportTimestamp, uint256 _preClValidators, uint256 _postClValidators, uint256 _postClBalance) public returns (uint256) {
        return _processClStateUpdate(_reportTimestamp, _preClValidators, _postClValidators, _postClBalance);
    }

    function collectRewardsAndProcessWithdrawals(
        OracleReportContracts memory _contracts,
        uint256 _withdrawalsToWithdraw,
        uint256 _elRewardsToWithdraw,
        uint256[] _withdrawalFinalizationBatches,
        uint256 _simulatedShareRate,
        uint256 _etherToLockOnWithdrawalQueue
    ) public {
            _collectRewardsAndProcessWithdrawals( _contracts, _withdrawalsToWithdraw, _elRewardsToWithdraw, _withdrawalFinalizationBatches, _simulatedShareRate, _etherToLockOnWithdrawalQueue);
    }

    function calculateWithdrawals(
        OracleReportContracts memory _contracts,
        OracleReportedData memory _reportedData
    ) public view returns (uint256, uint256) {
        return _calculateWithdrawals(_contracts, _reportedData);
    }

    function processRewards(
        OracleReportContext memory _reportContext,
        uint256 _postCLBalance,
        uint256 _withdrawnWithdrawals,
        uint256 _withdrawnElRewards
    ) public returns (uint256) {
        return _processRewards(_reportContext, _postCLBalance, _withdrawnWithdrawals, _withdrawnElRewards);
    }

    function distributeFee(
        uint256 _preTotalPooledEther,
        uint256 _preTotalShares,
        uint256 _totalRewards
    ) public returns (uint256) {
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

    function getTotalPooledEther() public view returns (uint256) {
        return _getTotalPooledEther();
    }

    function _completeTokenRebase(
        OracleReportedData memory _reportedData,
        OracleReportContext memory _reportContext,
        IPostTokenRebaseReceiver _postTokenRebaseReceiver
    ) public returns (uint256, uint256) {
        return _completeTokenRebase(_reportedData, _reportContext, _postTokenRebaseReceiver);
    }

    function loadOracleReportContracts() public view returns (OracleReportContracts memory ret) {
        return loadOracleReportContracts();
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

    // The following two functions are a workaround to get the value of the stakingRouter summarized function:
    function getStakingModuleMaxDepositsCount_workaround(uint256 a, uint256 b) public returns (uint256) {
        return getStakingModuleMaxDepositsCount(a, b);
    }

    function getStakingModuleMaxDepositsCount(uint256 a, uint256 b) private returns (uint256) {
        return a+ b;
    }
}