certoraRun \
./certora/harness/MinFirstAllocationStrategyTest.sol \
--verify MinFirstAllocationStrategyTest:certora/specs/Libraries/MinFirstAllocation.spec \
\
--solc solc8.9 \
--loop_iter 4 \
--cloud master \
--optimistic_loop \
--send_only \
--msg "MinFirstAllocationStrategyTest"