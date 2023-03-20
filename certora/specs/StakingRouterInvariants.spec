import "./StakingRouterBase.spec"
import "./NodeRegistryMethods.spec"

using StakingRouterHarness as SR

invariant modulesCountIsLastIndex()
    getLastStakingModuleId() == getStakingModulesCount()

invariant StakingModuleIdLELast(uint256 moduleId)
    getStakingModuleIdById(moduleId) <= getLastStakingModuleId()
    filtered{f -> !isDeposit(f)}

invariant StakingModuleIndexIsIdMinus1(uint256 moduleId)
    ((moduleId <= getStakingModulesCount() && moduleId > 0)
        => 
    (getStakingModuleIndexOneBased(moduleId) == moduleId))
     
     &&
    
    ((moduleId > getStakingModulesCount() || moduleId == 0)
        => 
    (getStakingModuleIndexOneBased(moduleId) == 0))
    filtered{f -> !isDeposit(f)}
    {
        preserved{
            requireInvariant StakingModuleIdLELast(moduleId);
            requireInvariant modulesCountIsLastIndex();
            requireInvariant StakingModuleIndexIsIdMinus1(getStakingModulesCount());
        }
    }

invariant StakingModuleId(uint256 moduleId)
    (moduleId <= getStakingModulesCount() => getStakingModuleIdById(moduleId) == moduleId)
    &&
    (moduleId > getStakingModulesCount() => getStakingModuleIdById(moduleId) == 0)
    filtered{f -> !isDeposit(f)}
    {
        preserved{
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
            requireInvariant StakingModuleIndexIsIdMinus1(getStakingModulesCount());
            requireInvariant StakingModuleIndexIsIdMinus1(to_uint256(getStakingModulesCount()+1));
            requireInvariant StakingModuleIdLELast(moduleId);
            requireInvariant modulesCountIsLastIndex();
            requireInvariant StakingModuleId(getStakingModulesCount());
        }
    }



invariant StakingModuleAddressIsNeverZero(uint256 moduleId)
    moduleId > 0 =>
    ((moduleId <= getLastStakingModuleId()) <=>
    getStakingModuleAddressById(moduleId) != 0)
    filtered{f -> !isDeposit(f)}
    {
        preserved{
            requireInvariant StakingModuleId(moduleId);
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
            requireInvariant StakingModuleIndexIsIdMinus1(getStakingModulesCount());
            requireInvariant modulesCountIsLastIndex();
        }
    }

invariant ZeroAddressForUnRegisteredModule(uint256 moduleId)
    moduleId > getStakingModulesCount() => getStakingModuleAddressById(moduleId) == 0
    filtered{f -> !isDeposit(f)}
    {
        preserved {
            requireInvariant modulesCountIsLastIndex();
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
            requireInvariant StakingModuleId(moduleId);
        }
    }

invariant StakingModuleAddressIsUnique(uint256 moduleId1, uint256 moduleId2)
    moduleId1 != moduleId2 =>
    differentOrEqualToZero_Address(getStakingModuleAddressById(moduleId1),getStakingModuleAddressById(moduleId2))
    filtered{f -> !isDeposit(f)}
    {
        preserved{
            requireInvariant StakingModuleId(moduleId1); 
            requireInvariant StakingModuleId(moduleId2); 
            requireInvariant modulesCountIsLastIndex();
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId1);
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId2);
            requireInvariant ZeroAddressForUnRegisteredModule(moduleId1);
            requireInvariant ZeroAddressForUnRegisteredModule(moduleId2);
        }
    }

invariant StakingModuleTargetShareLEMAX(uint256 moduleId) 
    getStakingModuleTargetShareById(moduleId) <= TOTAL_BASIS_POINTS()
    filtered{f -> !isDeposit(f)}

invariant StakingModuleTotalFeeLEMAX(uint256 moduleId)
    getStakingModuleFeeById(moduleId) + getStakingModuleTreasuryFeeById(moduleId) <= TOTAL_BASIS_POINTS()
    filtered{f -> !isDeposit(f)}

invariant UnRegisteredStakingModuleIsActive(uint256 moduleId)
    moduleId > getStakingModulesCount() => getStakingModuleIsActive(moduleId)
    filtered{f -> !isDeposit(f)}

invariant ZeroExitedValidatorsForUnRegisteredModule(uint256 moduleId)
    moduleId > getStakingModulesCount() => getStakingModuleExitedValidatorsById(moduleId) == 0 
    filtered{f -> !isDeposit(f)}
    {
        preserved {
            requireInvariant modulesCountIsLastIndex();
            requireInvariant StakingModuleIdLELast(moduleId);
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
            requireInvariant StakingModuleIndexIsIdMinus1(getStakingModulesCount());
            requireInvariant StakingModuleId(moduleId);
        }
        preserved unsafeSetExitedValidatorsCount(
            uint256 _moduleId, uint256 operatorId, bool trigger, SR.ValidatorsCountsCorrection correction) with (env e) {
                requireInvariant modulesCountIsLastIndex();
                requireInvariant StakingModuleIndexIsIdMinus1(_moduleId);
                requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
                requireInvariant StakingModuleId(_moduleId);
                requireInvariant StakingModuleId(moduleId);
            }
        preserved updateExitedValidatorsCountByStakingModule(uint256[] ids, uint256[] counts) with (env e) {
            require ids.length == 2;
            requireInvariant modulesCountIsLastIndex();
            requireInvariant StakingModuleIndexIsIdMinus1(ids[0]);
            requireInvariant StakingModuleIndexIsIdMinus1(ids[1]);
            requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
            requireInvariant StakingModuleId(ids[0]);
            requireInvariant StakingModuleId(ids[1]);
            requireInvariant StakingModuleId(moduleId);
        }
    }
function differentOrEqualToZero_Address(address a, address b) returns bool {
    return a != b || (a == 0 || b == 0);
}

function safeAssumptions(uint256 moduleId) {
    requireInvariant modulesCountIsLastIndex();
    if(moduleId > 0) {
        requireInvariant ZeroAddressForUnRegisteredModule(moduleId);
        requireInvariant StakingModuleIdLELast(moduleId);
        requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
        requireInvariant StakingModuleId(moduleId);
        requireInvariant StakingModuleAddressIsNeverZero(moduleId);
        requireInvariant StakingModuleTotalFeeLEMAX(moduleId);
        requireInvariant StakingModuleTargetShareLEMAX(moduleId);
        requireInvariant ZeroExitedValidatorsForUnRegisteredModule(moduleId);
        requireInvariant StakingModuleAddressIsUnique(moduleId, getStakingModulesCount());
    }
}
