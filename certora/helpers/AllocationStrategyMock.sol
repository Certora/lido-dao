// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0

/* See contracts/COMPILERS.md */
// solhint-disable-next-line
pragma solidity >=0.4.24 <0.9.0;

library MinFirstAllocationStrategy {
    uint256 private constant MAX_UINT256 = 2**256 - 1;

    function allocate(
        uint256[] memory buckets,
        uint256[] memory capacities,
        uint256 allocationSize
    ) internal pure returns (uint256 allocated) {
        uint256 globalMax = MAX_UINT256 - allocationSize;
        uint256 increment;
        for (uint256 i; i < buckets.length; ++i) {
            if(allocationSize == allocated) break;
            if(buckets[i] >= capacities[i]) continue;

            uint256 maxIncrement = min(globalMax, capacities[i] - buckets[i]);
            if(maxIncrement + allocated <= allocationSize) {
                increment = maxIncrement;
            }
            else if(maxIncrement/2 + allocated <= allocationSize) {
                increment = maxIncrement/2;
            }
            else {
                increment = 0;
            }
            buckets[i] += increment;
            allocated += increment;
        }
    }

    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
}