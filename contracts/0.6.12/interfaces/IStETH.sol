// SPDX-License-Identifier: NONE

pragma solidity 0.6.12; // latest available for using OZ

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";


interface IStETH is IERC20 {
    function getPooledEthByShares(uint256 _sharesAmount) external view returns (uint256);

    function getSharesByPooledEth(uint256 _pooledEthAmount) external view returns (uint256);
}