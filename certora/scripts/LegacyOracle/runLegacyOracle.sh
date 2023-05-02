certoraRun \
./contracts/0.4.24/oracle/LegacyOracle.sol \
./contracts/0.8.9/oracle/HashConsensus.sol \
--verify LegacyOracle:certora/specs/LegacyOracle/LegacyOracle.spec \
\
\
--solc_map HashConsensus=solc8.9,LegacyOracle=solc4.24 \
--loop_iter 3 \
--cloud master \
--optimistic_loop \
--send_only \
--rule_sanity \
--settings -t=500,-mediumTimeout=100,-depth=12,-copyLoopUnroll=5,-optimisticUnboundedHashing=true,-contractRecursionLimit=1 \
--msg "Legacy Oracle"