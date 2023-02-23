certoraRun \
./certora/harness/StakingRouter.sol:StakingRouterHarness \
./contracts/0.4.24/test_helpers/DepositContractMock.sol \
./certora/munged/NodeOperatorsRegistry.sol \
./contracts/0.8.9/Burner.sol \
./contracts/0.8.9/LidoLocator.sol \
./certora/harness/LidoMockStEth.sol \
--verify StakingRouterHarness:certora/specs/StakingRouter.spec \
\
\
--link StakingRouterHarness:DEPOSIT_CONTRACT=DepositContractMock \
LidoLocator:burner=Burner \
LidoLocator:lido=LidoMockStEth \
\
\
--solc_map StakingRouterHarness=solc8.9,Burner=solc8.9,LidoLocator=solc8.9,\
NodeOperatorsRegistry=solc4.24,LidoMockStEth=solc4.24,DepositContractMock=solc4.24 \
--loop_iter 2 \
--staging master \
--optimistic_loop \
--send_only \
--settings -t=600,-mediumTimeout=50,-copyLoopUnroll=5,-optimisticUnboundedHashing=true \
--msg "Staking Router"