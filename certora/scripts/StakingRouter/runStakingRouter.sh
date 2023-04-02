certoraRun \
./certora/harness/StakingRouter.sol:StakingRouterHarness \
./certora/munged/NodeOperatorsRegistry.sol \
./contracts/0.8.9/Burner.sol \
./contracts/0.8.9/LidoLocator.sol \
./certora/harness/LidoMockStEth.sol \
./contracts/0.8.9/test_helpers/StakingModuleMock.sol \
--verify StakingRouterHarness:certora/specs/StakingRouter/StakingRouter.spec \
\
\
--link \
LidoLocator:burner=Burner \
LidoLocator:lido=LidoMockStEth \
\
\
--solc_map StakingRouterHarness=solc8.9,Burner=solc8.9,LidoLocator=solc8.9,\
StakingModuleMock=solc8.9,\
NodeOperatorsRegistry=solc4.24,LidoMockStEth=solc4.24 \
--loop_iter 4 \
--optimistic_loop \
--staging pre_cvl2 \
--rule_sanity \
--send_only \
--settings -optimisticFallback=true \
--settings -t=1200,-depth=12,-mediumTimeout=100,-copyLoopUnroll=6,-optimisticUnboundedHashing=true \
--msg "Staking Router"