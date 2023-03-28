pragma solidity 0.4.24;

import "../../contracts/0.4.24/Lido.sol";

contract LidoHarness is Lido {
    function getMaxRebase(address a) public view returns(uint256)
    {
        return IOracleReportSanityChecker(a).getMaxPositiveTokenRebase();
    }
    function getCLbalance() external view returns(uint256)
    {
        return CL_BALANCE_POSITION.getStorageUint256();
    }
    function getCLvalidators() external view returns(uint256)
    {
        return CL_VALIDATORS_POSITION.getStorageUint256();
    }

    function getRatio() external view returns(uint256)
    {
        return getPooledEthByShares(1e18);
    }

    function getTotalAssetEth() external view returns(uint256)
    {
        return _getTotalPooledEther();
    }

    function getTotalShares() external view returns(uint256)
    {
        return _getTotalShares();
    }
    function t() external{
        _loadOracleReportContracts();
    }
}