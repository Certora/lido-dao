// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0

/* See contracts/COMPILERS.md */
pragma solidity 0.8.9;

import "../munged/DepositSecurityModule.sol";


contract DepositSecurityModuleHarness is DepositSecurityModule {
    constructor(
        address _lido,
        address _depositContract,
        address _stakingRouter,
        uint256 _maxDepositsPerBlock,
        uint256 _minDepositBlockDistance,
        uint256 _pauseIntentValidityPeriodBlocks
    ) DepositSecurityModule(
        _lido, 
        _depositContract, 
        _stakingRouter, 
        _maxDepositsPerBlock, 
        _minDepositBlockDistance, 
        _pauseIntentValidityPeriodBlocks
    ) { }

    function getGuardian(uint256 index) external view returns (address) {
        return index < guardians.length ? guardians[index] : address(0);
    }

    function getGuardiansLength() external view returns (int256) {
        return int(guardians.length);
    }

    Signature[] sortedGuardianSignatures;

    function depositBufferedEtherCall(
        uint256 blockNumber,
        bytes32 blockHash,
        bytes32 depositRoot,
        uint256 stakingModuleId,
        uint256 nonce,
        bytes calldata depositCalldata
    ) external {
        depositBufferedEther(
            blockNumber,
            blockHash,
            depositRoot,
            stakingModuleId,
            nonce,
            depositCalldata,
            sortedGuardianSignatures
        );
    }

    function getHashedAddress(
        uint256 blockNumber,
        uint256 stakingModuleId,
        Signature memory sig
    ) external returns (address) {
        bytes32 msgHash = keccak256(abi.encodePacked(PAUSE_MESSAGE_PREFIX, blockNumber, stakingModuleId));
        return ECDSA.recover(msgHash, sig.r, sig.vs);
    }

    function getEthBalance(address addr) external view returns (uint256) {
        return address(addr).balance;
    }
}
