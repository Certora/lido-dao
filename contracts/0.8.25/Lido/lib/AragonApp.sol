// SPDX-FileCopyrightText: 2025 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0

pragma solidity 0.8.25;

import {UnstructuredStorage} from "./UnstructuredStorage.sol";

/**
 * @title IACL
 * @dev Interface for Aragon ACL contract
 */
interface IACL {
    function hasPermission(address who, address where, bytes32 what, bytes calldata how) external view returns (bool);
}

/**
 * @title IKernel
 * @dev Interface for Aragon Kernel contract
 */
interface IKernel {
    function acl() external view returns (IACL);
}

/**
 * @title AragonApp
 * @dev Minimal Aragon App implementation for Solidity 0.8.25
 *      Provides initialization pattern and ACL integration
 */
abstract contract AragonApp {
    using UnstructuredStorage for bytes32;

    // keccak256("aragonOS.appStorage.kernel")
    bytes32 internal constant KERNEL_POSITION =
        0x4172f0f7d2289153072b0a6ca36959e0cbe2efc3afe50fc81636caa96338137b;

    // keccak256("aragonOS.appStorage.appId")
    bytes32 internal constant APP_ID_POSITION =
        0xd625496217aa6a3453eecb9c3489dc5a53e6c67b444329ea2b2cbc9ff547639b;

    // keccak256("aragonOS.initializable.initializationBlock")
    bytes32 internal constant INITIALIZATION_BLOCK_POSITION =
        0xebb05b386a8d34882b8711d156f463690983dc47815980fb82aeeff1aa43579e;

    modifier onlyInit() {
        require(INITIALIZATION_BLOCK_POSITION.getStorageUint256() == 0, "INIT_ALREADY_INITIALIZED");
        _;
    }

    modifier isInitialized() {
        require(hasInitialized(), "INIT_NOT_INITIALIZED");
        _;
    }

    /**
     * @dev Sets initialization block
     */
    function initialized() internal {
        INITIALIZATION_BLOCK_POSITION.setStorageUint256(block.number);
    }

    /**
     * @return Whether the contract has been initialized
     */
    function hasInitialized() public view returns (bool) {
        return INITIALIZATION_BLOCK_POSITION.getStorageUint256() != 0;
    }

    /**
     * @notice Returns the kernel associated with this app
     */
    function kernel() public view returns (IKernel) {
        return IKernel(KERNEL_POSITION.getStorageAddress());
    }

    /**
     * @dev Sets the kernel address
     */
    function setKernel(address _kernel) internal {
        KERNEL_POSITION.setStorageAddress(_kernel);
    }

    /**
     * @notice Checks if a user can perform an action
     * @param _sender The address attempting to perform the action
     * @param _role The role identifier (permission)
     * @param _params Additional parameters for the permission check (unused in this implementation)
     * @return Whether the sender has permission
     */
    function canPerform(address _sender, bytes32 _role, uint256[] memory _params) public view returns (bool) {
        IKernel _kernel = kernel();
        if (address(_kernel) == address(0)) {
            return false;
        }

        IACL acl = _kernel.acl();
        if (address(acl) == address(0)) {
            return false;
        }

        return acl.hasPermission(_sender, address(this), _role, new bytes(0));
    }

    /**
     * @notice Override for token recovery - disabled by default
     */
    function transferToVault(address /* _token */) external virtual {
        revert("NOT_SUPPORTED");
    }
}
