import "./StakingRouterBase.spec"
import "./NodeRegistryMethods.spec"


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
        }
    }

invariant zeroAddressForUnRegisteredModule(uint256 moduleId)
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
            requireInvariant zeroAddressForUnRegisteredModule(moduleId1);
            requireInvariant zeroAddressForUnRegisteredModule(moduleId2);
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

invariant AddressesByIndexAndIdAreEqual(uint256 moduleId)
    moduleId > 0 =>
    getStakingModuleAddressById(moduleId) == 
    getStakingModuleAddressByIndex(moduleId-1)
    filtered{f -> !isDeposit(f)}
    {
        preserved{
            safeAssumptions(moduleId);
            requireInvariant StakingModuleIndexIsIdMinus1(
                to_uint256(getStakingModulesCount())
            );
            requireInvariant StakingModuleId(
                to_uint256(getStakingModulesCount())
            );
        }
    }


function differentOrEqualToZero_Address(address a, address b) returns bool {
    return a != b || (a == 0 || b == 0);
}

function safeAssumptions(uint256 moduleId) {
    requireInvariant modulesCountIsLastIndex();
    if(moduleId > 0) {
        requireInvariant zeroAddressForUnRegisteredModule(moduleId);
        requireInvariant StakingModuleIdLELast(moduleId);
        requireInvariant StakingModuleIndexIsIdMinus1(moduleId);
        requireInvariant StakingModuleId(moduleId);
        requireInvariant StakingModuleAddressIsNeverZero(moduleId);
        requireInvariant StakingModuleTotalFeeLEMAX(moduleId);
        requireInvariant StakingModuleTargetShareLEMAX(moduleId);
        requireInvariant AddressesByIndexAndIdAreEqual(moduleId);
        requireInvariant StakingModuleAddressIsUnique(moduleId, getStakingModulesCount());
    }
}
