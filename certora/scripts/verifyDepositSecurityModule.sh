if [[ "$1" ]]
then
    RULE="--rule $1"
fi

if [[ "$2" ]]
then
    MSG="- $2"
fi

certoraRun \
    contracts/0.8.9/DepositSecurityModule.sol \
    contracts/0.8.9/StakingRouter.sol \
    contracts/0.8.9/LidoLocator.sol \
    contracts/0.8.9/test_helpers/StakingModuleMock.sol \
    \
    contracts/0.4.24/Lido.sol \
    contracts/0.4.24/test_helpers/DepositContractMock.sol \
    \
    certora/harnesses/WithdrawalQueueHarness.sol \
    \
    --verify DepositSecurityModule:certora/specs/DepositSecurityModule.spec \
    --solc_map StakingModuleMock=solc8.9,DepositSecurityModule=solc8.9,StakingRouter=solc8.9,WithdrawalQueueHarness=solc8.9,LidoLocator=solc8.9,Lido=solc4.24,DepositContractMock=solc4.24 \
    --optimistic_loop \
    --loop_iter 3 \
    --send_only \
    --rule_sanity \
    --staging master \
    $RULE \
    --msg "DepositSecurityModule: $RULE $MSG"