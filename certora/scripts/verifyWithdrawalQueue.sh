certoraRun certora/harness/WithdrawalQueueHarness.sol \
    --verify WithdrawalQueueHarness:certora/specs/WithdrawalQueue.spec \
    --optimistic_loop \
    --solc solc8.9 \
    --staging \
    --loop_iter 3 \
    --settings -optimisticFallback=true \
    --msg "WithdrawalQueue - all rules1"