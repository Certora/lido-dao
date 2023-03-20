if [[ "$1" ]]
then
    RULE="--rule $1"
fi

if [[ "$2" ]]
then
    MSG="- $2"
fi

certoraRun \
    contracts/0.8.9/oracle/ValidatorsExitBusOracle.sol \
    --verify ValidatorsExitBusOracle:certora/specs/ValidatorsExitBusOracle.spec \
    --solc solc8.9 \
    --optimistic_loop \
    --loop_iter 3 \
    --send_only \
    --rule_sanity \
    --staging master \
    $RULE \
    --msg "ValidatorsExitBusOracle: $RULE $MSG"


# certoraRun \
#     certora/harnesses/DepositSecurityModuleHarness.sol \
#     contracts/0.8.9/StakingRouter.sol \
#     contracts/0.8.9/LidoLocator.sol \
#     contracts/0.8.9/BeaconChainDepositor.sol \
#     \
#     contracts/0.4.24/nos/NodeOperatorsRegistry.sol \
#     contracts/0.4.24/Lido.sol \
#     \
#     certora/harnesses/WithdrawalQueueHarness.sol \
#     \
#     --verify DepositSecurityModuleHarness:certora/specs/DepositSecurityModule.spec \
#     --solc_map BeaconChainDepositor=solc8.9,DepositSecurityModuleHarness=solc8.9,StakingRouter=solc8.9,WithdrawalQueueHarness=solc8.9,LidoLocator=solc8.9,Lido=solc4.24,NodeOperatorsRegistry=solc4.24 \
#     --link DepositSecurityModuleHarness:LIDO=Lido \
#     --optimistic_loop \
#     --loop_iter 2 \
#     --send_only \
#     --rule_sanity \
#     --staging master \
#     --settings -t=2000,-mediumTimeout=2000,-depth=100,-copyLoopUnroll=6 \
#     $RULE \
#     --msg "DepositSecurityModule: $RULE $MSG"


# contracts/0.4.24/test_helpers/DepositContractMock.sol \
# DepositContractMock=solc4.24

# contracts/0.8.9/DepositSecurityModule.sol \

# contracts/0.8.9/test_helpers/StakingModuleMock.sol \