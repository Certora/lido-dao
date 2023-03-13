// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>

// SPDX-License-Identifier: GPL-3.0

/* See contracts/COMPILERS.md */
pragma solidity 0.8.9;

import {StakingRouter} from "../munged/StakingRouter.sol";
import {UnstructuredStorage} from "../../contracts/0.8.9/lib/UnstructuredStorage.sol";

contract StakingRouterHarness is StakingRouter {
    using UnstructuredStorage for bytes32;

    constructor(
        address admin, 
        address lido, 
        bytes32 withdrawalCredentials, 
        address depositContract) 
        StakingRouter(depositContract) {
            initialize(admin, lido, withdrawalCredentials);
        }

    function getStakingModuleAddressByIndex(uint256 _stakingModuleIndex) public view returns (address) {
        return _getStakingModuleAddressByIndex(_stakingModuleIndex);
    }

    function getStakingModuleAddressById(uint256 _stakingModuleId) public view returns (address) {
        if(_stakingModuleId == 0){
            return address(0);
        }
        StakingModule storage stakingModule = _getStakingModuleByIndex(_stakingModuleId-1);
        return stakingModule.stakingModuleAddress;
    }

    function getStakingModuleExitedValidatorsById(uint256 _stakingModuleId) public view returns (uint256) {
        if(_stakingModuleId == 0){
            return 0;
        }
        StakingModule storage stakingModule = _getStakingModuleByIndex(_stakingModuleId-1);
        return stakingModule.exitedValidatorsCount;
    }

    function getStakingModuleIdById(uint256 _stakingModuleId) public view returns (uint256) {
        if(_stakingModuleId == 0){
            return 0;
        }
        StakingModule storage stakingModule = _getStakingModuleByIndex(_stakingModuleId-1);
        return stakingModule.id;
    }

    function getStakingModuleFeeById(uint256 _stakingModuleId) public view returns (uint16) {
        if(_stakingModuleId == 0){
            return 0;
        }
        StakingModule storage stakingModule = _getStakingModuleByIndex(_stakingModuleId-1);
        return stakingModule.stakingModuleFee;
    }
    
    function getStakingModuleTreasuryFeeById(uint256 _stakingModuleId) public view returns (uint16) {
        if(_stakingModuleId == 0){
            return 0;
        }
        StakingModule storage stakingModule = _getStakingModuleByIndex(_stakingModuleId-1);
        return stakingModule.treasuryFee;
    }

    function getStakingModuleTargetShareById(uint256 _stakingModuleId) public view returns (uint16) {
        if(_stakingModuleId == 0){
            return 0;
        }
        StakingModule storage stakingModule = _getStakingModuleByIndex(_stakingModuleId-1);
        return stakingModule.targetShare;
    }

    function getStakingModuleNameLengthByIndex(uint256 index) public view returns (uint256) {
        StakingModule storage stakingModule = _getStakingModuleByIndex(index);
        return bytes(stakingModule.name).length;
    }

    function getStakingModuleIndexOneBased(uint256 _stakingModuleId) public view returns (uint256) {
        mapping(uint256 => uint256) storage _stakingModuleIndicesOneBased = _getStorageStakingIndicesMapping();
        return _stakingModuleIndicesOneBased[_stakingModuleId];
    }

    function getLastStakingModuleId() public view returns (uint24) {
        return uint24(LAST_STAKING_MODULE_ID_POSITION.getStorageUint256());
    }
}
