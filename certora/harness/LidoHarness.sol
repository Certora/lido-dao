pragma solidity 0.4.24;

import "../../contracts/0.4.24/Lido.sol";

contract LidoHarness is Lido {
    function getIsStopped() public view returns (bool) {
        return isStopped();
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