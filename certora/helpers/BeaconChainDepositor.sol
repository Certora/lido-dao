// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0

// See contracts/COMPILERS.md
pragma solidity 0.8.9;

import {BeaconChainDepositor} from "../munged/BeaconChainDepositor.sol";

contract BeaconChainDepositorHarness is BeaconChainDepositor {

    // Certora replacements for MemUtils
    // signatures batch => index => signature
    mapping(bytes => mapping(uint256 => Signature)) private signatures;
    // public keys batch => index => public key
    mapping(bytes => mapping(uint256 => PublicKey)) private public_keys;
    mapping(bytes => bytes32) private _publicKeyRoot;
    mapping(bytes => bytes32) private _signatureRoot;

    struct Signature {
        bytes32 a;
        bytes32 b;
        bytes32 c;
    }

    struct PublicKey {
        bytes32 a;
        bytes16 b;
    }

    constructor(address _depositContract) BeaconChainDepositor(_depositContract) {}

    /// @notice Certora: change root-hashing functions to simple mappings.
    /// @dev Invokes a deposit call to the official Beacon Deposit contract
    /// @param _keysCount amount of keys to deposit
    /// @param _withdrawalCredentials Commitment to a public key for withdrawals
    /// @param _publicKeysBatch A BLS12-381 public keys batch
    /// @param _signaturesBatch A BLS12-381 signatures batch
    function _makeBeaconChainDeposits32ETH(
        uint256 _keysCount,
        bytes memory _withdrawalCredentials,
        bytes memory _publicKeysBatch,
        bytes memory _signaturesBatch
    ) internal override {
        if (_publicKeysBatch.length != PUBLIC_KEY_LENGTH * _keysCount) {
            revert InvalidPublicKeysBatchLength(_publicKeysBatch.length, PUBLIC_KEY_LENGTH * _keysCount);
        }
        if (_signaturesBatch.length != SIGNATURE_LENGTH * _keysCount) {
            revert InvalidSignaturesBatchLength(_signaturesBatch.length, SIGNATURE_LENGTH * _keysCount);
        }

        for (uint256 i; i < _keysCount;) {
            PublicKey memory pubkStruct = public_keys[_publicKeysBatch][i];
            Signature memory sigStruct = signatures[_signaturesBatch][i];

            bytes memory publicKey = abi.encodePacked(pubkStruct.a, pubkStruct.b);
            bytes memory signature = abi.encodePacked(sigStruct.a, sigStruct.b, sigStruct.c);

            DEPOSIT_CONTRACT.deposit{value: DEPOSIT_SIZE}(
                publicKey, _withdrawalCredentials, signature,
                _computeDepositDataRootCertora(_withdrawalCredentials, publicKey, signature)
            );
            
            unchecked {
                ++i;
            }
        }
    }

    /// @notice Certora: change root-hashing functions to simple mappings.
    /// @dev computes the deposit_root_hash required by official Beacon Deposit contract
    /// @param _publicKey A BLS12-381 public key.
    /// @param _signature A BLS12-381 signature
    function _computeDepositDataRootCertora(bytes memory _withdrawalCredentials, bytes memory _publicKey, bytes memory _signature)
        private
        view 
        returns (bytes32)
    {
        bytes32 publicKeyRoot = _publicKeyRoot[_publicKey];
        bytes32 signatureRoot = _signatureRoot[_signature];

        return sha256(
            abi.encodePacked(
                sha256(abi.encodePacked(publicKeyRoot, _withdrawalCredentials)),
                sha256(abi.encodePacked(DEPOSIT_SIZE_IN_GWEI_LE64, bytes24(0), signatureRoot))
            )
        );
    }
}
