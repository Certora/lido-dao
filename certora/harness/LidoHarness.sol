pragma solidity 0.4.24;

import "../../contracts/0.4.24/Lido.sol";

contract LidoHarness is Lido {
    // function getCLbalance() external view returns(uint256)
    // {
    //     return CL_VALIDATORS_POSITION.getStorageUint256();
    // }

    // function getRatio() external view returns(uint256)
    // {
    //     return getPooledEthByShares(1e18);
    // }

    function getIsStopped() public view returns (bool) {
        return isStopped();
    }
}