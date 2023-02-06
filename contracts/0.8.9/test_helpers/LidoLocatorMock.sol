// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>

// SPDX-License-Identifier: GPL-3.0

// See contracts/COMPILERS.md
pragma solidity 0.8.9;

import "../../common/interfaces/ILidoLocator.sol";

contract LidoLocatorMock is ILidoLocator {
    struct ContractAddresses {
        address lido;
        address depositSecurityModule;
        address elRewardsVault;
        address accountingOracle;
        address legacyOracle;
        address safetyNetsRegistry;
        address selfOwnedStEthBurner;
        address validatorExitBus;
        address stakingRouter;
        address treasury;
        address withdrawalQueue;
        address withdrawalVault;
        address postTokenRebaseReceiver;
    }

    address public immutable lido;
    address public immutable depositSecurityModule;
    address public immutable elRewardsVault;
    address public immutable accountingOracle;
    address public immutable legacyOracle;
    address public immutable safetyNetsRegistry;
    address public immutable selfOwnedStEthBurner;
    address public immutable validatorExitBus;
    address public immutable stakingRouter;
    address public immutable treasury;
    address public immutable withdrawalQueue;
    address public immutable withdrawalVault;
    address public immutable postTokenRebaseReceiver;

    constructor (
        ContractAddresses memory addrs
    ) {
        lido = addrs.lido;
        depositSecurityModule = addrs.depositSecurityModule;
        elRewardsVault = addrs.elRewardsVault;
        accountingOracle = addrs.accountingOracle;
        legacyOracle = addrs.legacyOracle;
        safetyNetsRegistry = addrs.safetyNetsRegistry;
        selfOwnedStEthBurner = addrs.selfOwnedStEthBurner;
        validatorExitBus = addrs.validatorExitBus;
        stakingRouter = addrs.stakingRouter;
        treasury = addrs.treasury;
        withdrawalQueue = addrs.withdrawalQueue;
        withdrawalVault = addrs.withdrawalVault;
        postTokenRebaseReceiver = addrs.postTokenRebaseReceiver;
    }

    function coreComponents() external view returns(address,address,address,address,address,address) {
        return (
            elRewardsVault,
            safetyNetsRegistry,
            stakingRouter,
            treasury,
            withdrawalQueue,
            withdrawalVault
        );
    }

}