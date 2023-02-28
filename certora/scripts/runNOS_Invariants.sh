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
--staging master \
--optimistic_loop \
--send_only \
--rule NodeOperatorsCountLEMAX \
--rule ActiveOperatorsLECount \
--rule AllModulesAreActiveConsistency \
--rule ExitedKeysLEDepositedKeys \
--rule DepositedKeysLEVettedKeys \
--rule VettedKeysLETotalKeys \
--rule SumOfDepositedKeysEqualsSummary \
--rule SumOfExitedKeysEqualsSummary \
--rule SumOfTotalKeysEqualsSummary \
--settings -t=750,-mediumTimeout=60,-depth=13,-copyLoopUnroll=5,-optimisticUnboundedHashing=true \
--msg "NodeOperatorsRegistry invariants"
# --staging yuvalbd/correct_param_count