import "./StakingRouterBase.spec"

methods {
    MANAGE_WITHDRAWAL_CREDENTIALS_ROLE() returns bytes32 envfree
    STAKING_MODULE_PAUSE_ROLE() returns bytes32 envfree
    STAKING_MODULE_RESUME_ROLE() returns bytes32 envfree
    STAKING_MODULE_MANAGE_ROLE() returns bytes32 envfree
    REPORT_EXITED_VALIDATORS_ROLE() returns bytes32 envfree
    UNSAFE_SET_EXITED_VALIDATORS_ROLE() returns bytes32 envfree
    REPORT_REWARDS_MINTED_ROLE() returns bytes32 envfree

    _auth(bytes32) => ALWAYS(true)
}

definition roleChangingMethods(method f) returns bool = 
    f.selector == revokeRole(bytes32,address).selector ||
    f.selector == renounceRole(bytes32,address).selector ||
    f.selector == grantRole(bytes32,address).selector;

function pickRole(uint8 ID) returns bytes32 {
    if(ID == 0) {return MANAGE_WITHDRAWAL_CREDENTIALS_ROLE();}
    else if(ID == 1) {return STAKING_MODULE_PAUSE_ROLE();}
    else if(ID == 2) {return STAKING_MODULE_RESUME_ROLE();}
    else if(ID == 3) {return STAKING_MODULE_MANAGE_ROLE();}
    else if(ID == 4) {return REPORT_EXITED_VALIDATORS_ROLE();}
    else if(ID == 5) {return UNSAFE_SET_EXITED_VALIDATORS_ROLE();}
    else if(ID == 6) {return REPORT_REWARDS_MINTED_ROLE();}
    else {return 0x0;}
}

function pickMethod(uint8 ID) returns uint32 {
    if(ID == 0) {return setWithdrawalCredentials(bytes32).selector;}
    else if(ID == 1) {return pauseStakingModule(uint256).selector;}
    else if(ID == 2) {return resumeStakingModule(uint256).selector;}
    else if(ID == 3) {return setStakingModuleStatus(uint256,uint8).selector;}
    else if(ID == 4) {return reportStakingModuleStuckValidatorsCountByNodeOperator(uint256,bytes,bytes).selector;}
    else if(ID == 5) {return unsafeSetExitedValidatorsCount(uint256,uint256,bool,(uint256,uint256,uint256,uint256,uint256,uint256)).selector;}
    else if(ID == 6) {return reportRewardsMinted(uint256[],uint256[]).selector;}
    else {return 0;}
}

function addressIsNotRole(address sender) returns bool {
    return !(
        hasRole(MANAGE_WITHDRAWAL_CREDENTIALS_ROLE(), sender) ||
        hasRole(STAKING_MODULE_PAUSE_ROLE(), sender) ||
        hasRole(STAKING_MODULE_RESUME_ROLE(), sender) ||
        hasRole(STAKING_MODULE_MANAGE_ROLE(), sender) ||
        hasRole(REPORT_EXITED_VALIDATORS_ROLE(), sender) ||
        hasRole(UNSAFE_SET_EXITED_VALIDATORS_ROLE(), sender) ||
        hasRole(REPORT_REWARDS_MINTED_ROLE(), sender)
        ); 
}

rule whichFunctionsRevertForUnauthorized(method f) 
filtered{f -> !f.isView && !roleChangingMethods(f) && !isDeposit(f)} {
    env e;
    calldataarg args;

    require addressIsNotRole(e.msg.sender);
    f@withrevert(e, args);

    assert lastReverted;
}

rule roleAuthorizationCheck(method f, uint8 ID) {
    require ID <= 6;
    
    uint32 roleMethod = pickMethod(ID);
    bytes32 role = pickRole(ID);

    env e;
    calldataarg args;
        f(e, args);
    assert f.selector == roleMethod => hasRole(role, e.msg.sender);
}

rule RolesChange(method f, bytes32 role, address sender) 
filtered{f -> !f.isView} {
    env e;
    calldataarg args;

    bool has_role_before = hasRole(role, sender);
        f(e, args);
    bool has_role_after = hasRole(role, sender);
    
    assert has_role_before != has_role_after => roleChangingMethods(f);
}
