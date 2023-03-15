certoraRun \
./certora/harness/StakingRouter.sol:StakingRouterHarness \
./contracts/0.6.11/deposit_contract.sol:DepositContract \
./certora/munged/NodeOperatorsRegistry.sol \
./contracts/0.8.9/Burner.sol \
./contracts/0.8.9/LidoLocator.sol \
./certora/harness/LidoMockStEth.sol \
./contracts/0.8.9/test_helpers/StakingModuleMock.sol \
--verify StakingRouterHarness:certora/specs/StakingRouter.spec \
\
\
--link \
LidoLocator:burner=Burner \
LidoLocator:lido=LidoMockStEth \
\
\
--solc_map StakingRouterHarness=solc8.9,Burner=solc8.9,LidoLocator=solc8.9,\
DepositContract=solc6.11,StakingModuleMock=solc8.9,\
NodeOperatorsRegistry=solc4.24,LidoMockStEth=solc4.24 \
--loop_iter 4 \
--cloud master \
--optimistic_loop \
--rule_sanity \
--send_only \
--settings -t=1600,-depth=12,-mediumTimeout=50,-copyLoopUnroll=6,-optimisticUnboundedHashing=true \
--msg "Staking Router "