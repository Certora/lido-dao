if [[ "$1" ]]
then
    RULE="--rule $1"
fi

if [[ "$2" ]]
then
    MSG="- $2"
fi

certoraRun \
    certora/harnesses/DepositSecurityModuleHarness.sol \
    certora/munged/0.8.9/StakingRouter.sol \
    certora/munged/0.8.9/LidoLocator.sol \
    \
    certora/munged/0.4.24/nos/NodeOperatorsRegistry.sol \
    certora/munged/0.4.24/Lido.sol \
    \
    certora/harnesses/WithdrawalQueueHarness.sol \
    \
    --verify DepositSecurityModuleHarness:certora/specs/DepositSecurityModule.spec \
    --solc_map DepositSecurityModuleHarness=solc8.9,StakingRouter=solc8.9,WithdrawalQueueHarness=solc8.9,LidoLocator=solc8.9,Lido=solc4.24,NodeOperatorsRegistry=solc4.24 \
    --link DepositSecurityModuleHarness:LIDO=Lido \
    --optimistic_loop \
    --loop_iter 3 \
    --send_only \
    --rule_sanity \
    --settings -optimisticUnboundedHashing=true,-optimisticFallback=true \
    --staging pre_cvl2 \
    --settings -t=2000,-mediumTimeout=2000,-depth=100,-copyLoopUnroll=6 \
    $RULE \
    --msg "DepositSecurityModule: $RULE $MSG"


# contracts/0.4.24/test_helpers/DepositContractMock.sol \
# DepositContractMock=solc4.24

# contracts/0.8.9/DepositSecurityModule.sol \

# contracts/0.8.9/test_helpers/StakingModuleMock.sol \