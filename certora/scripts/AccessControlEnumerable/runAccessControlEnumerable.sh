certoraRun \
./certora/harness/AccessControlEnumerableTest.sol \
--verify AccessControlEnumerableTest:certora/specs/AccessControlEnumerable/AccessControlEnumerable.spec \
\
\
--solc_map AccessControlEnumerableTest=solc8.9 \
--loop_iter 3 \
--cloud pre_cvl2 \
--optimistic_loop \
--send_only \
--rule_sanity advanced \
--msg "AccessControlEnumerableTest"