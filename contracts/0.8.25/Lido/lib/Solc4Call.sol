// SPDX-FileCopyrightText: 2025 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0

pragma solidity 0.8.25;

/// @title Solc4Call library
/// @notice Wraps external staticcalls with Solidity 0.4-style behavior:
///         cleans dirty bits instead of reverting, no strict ABI validation
library Solc4Call {
    /// @notice Make a staticcall and return the result as a cleaned address
    /// @param _target The contract to call (cleaned to 160 bits)
    /// @param _data The calldata (use abi.encodeWithSelector)
    /// @return The returned address, cleaned to 160 bits
    function staticcallAddress(address _target, bytes memory _data) internal view returns (address) {
        uint256 result = _staticcall(_target, _data);
        return address(uint160(result));
    }

    /// @notice Make a staticcall and return the result as uint256
    /// @param _target The contract to call (cleaned to 160 bits)
    /// @param _data The calldata (use abi.encodeWithSelector)
    /// @return The returned uint256
    function staticcallUint256(address _target, bytes memory _data) internal view returns (uint256) {
        return _staticcall(_target, _data);
    }

    /// @notice Make a staticcall and return the result as a cleaned uint16
    /// @param _target The contract to call (cleaned to 160 bits)
    /// @param _data The calldata (use abi.encodeWithSelector)
    /// @return The returned value, cleaned to 16 bits
    function staticcallUint16(address _target, bytes memory _data) internal view returns (uint16) {
        uint256 result = _staticcall(_target, _data);
        return uint16(result);
    }

    /// @notice Make a staticcall and return the raw 32-byte result
    /// @param _target The contract to call (cleaned to 160 bits)
    /// @param _data The calldata (use abi.encodeWithSelector)
    /// @return The raw 32-byte return value
    function staticcallBytes32(address _target, bytes memory _data) internal view returns (bytes32) {
        return bytes32(_staticcall(_target, _data));
    }

    /// @dev Internal function that performs the staticcall and returns raw uint256
    function _staticcall(address _target, bytes memory _data) private view returns (uint256 result) {
        assembly {
            // Clean target address to 160 bits (Solidity 0.4 style)
            _target := and(_target, 0xffffffffffffffffffffffffffffffffffffffff)

            // Check that target has code
            if iszero(extcodesize(_target)) {
                revert(0, 0)
            }

            // Get free memory pointer for output
            let ptr := mload(0x40)

            // Perform staticcall
            // _data layout: first 32 bytes = length, then actual data
            let success := staticcall(
                gas(),
                _target,
                add(_data, 32),    // skip length prefix
                mload(_data),      // length of data
                ptr,               // output at free memory pointer
                32                 // expect 32 bytes output
            )

            // If call failed, revert with original error data
            if iszero(success) {
                returndatacopy(0, 0, returndatasize())
                revert(0, returndatasize())
            }

            // Check that return data is at least 32 bytes
            if lt(returndatasize(), 32) {
                revert(0, 0)
            }

            // Load result from output location
            result := mload(ptr)
        }
    }
}
