// Staking router
// The StakingRouter contract is responsible for:

// plugging validator subsets modules together
// distribute new ether for staking to modules
// distribute accrued rewards between modules
// push ether together with signed keys to the DepositContract (Beacon Deposit Contract)
// NodeOperatorsRegistry has the updated interface to be a pluggable module for StakingRouter.

// There is also a separate contract that mitigates deposit front-running vulnerability DepositSecurityModule.


methods {
    addModule(string,address,uint16,uint16,uint16)
    getStakingModulesCount() returns (uint256) envfree
}

rule sanity(){
    assert false;
}

rule addModuleIntegrity(string name, address moduleAddress, uint16 targetShare, 
    uint16 moduleFee, uint16 treasuryFee) {
        env e;
        uint modulesCountBefore = getStakingModulesCount();
        addModule(e, name, moduleAddress, targetShare, moduleFee, treasuryFee);
        uint modulesCountAfter = getStakingModulesCount();
        assert modulesCountAfter == modulesCountBefore + 1;
}
