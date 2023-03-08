certoraRun \
./certora/harness/NodeOperatorsRegistry.sol:NodeOperatorsRegistryHarness \
./contracts/0.8.9/Burner.sol \
./certora/harness/LidoMockStEth.sol \
--verify NodeOperatorsRegistryHarness:certora/specs/NodeOperatorsRegistry.spec \
\
\
\
--solc_map Burner=solc8.9,NodeOperatorsRegistryHarness=solc4.24,LidoMockStEth=solc4.24 \
--loop_iter 2 \
--staging master \
--optimistic_loop \
--send_only \
--settings -t=1500,-mediumTimeout=30,-depth=12,-copyLoopUnroll=5,-optimisticUnboundedHashing=true \
--settings -solvers=[cvc5,z3] \
--msg "NodeOperatorsRegistry"
# --staging yuvalbd/correct_param_count
