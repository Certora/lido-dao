certoraRun \
./certora/harness/NodeOperatorsRegistry.sol:NodeOperatorsRegistryHarness \
./contracts/0.8.9/Burner.sol \
./certora/harness/LidoMockStEth.sol \
--verify NodeOperatorsRegistryHarness:certora/specs/NodeOperatorsRegistry.spec \
\
\
\
--solc_map Burner=solc8.9,NodeOperatorsRegistryHarness=solc4.24,LidoMockStEth=solc4.24 \
--loop_iter 3 \
--cloud master \
--optimistic_loop \
--send_only \
--rule_sanity \
--settings -t=2000,-mediumTimeout=120,-depth=10,-copyLoopUnroll=5,-optimisticUnboundedHashing=true \
--msg "NodeOperatorsRegistry"
