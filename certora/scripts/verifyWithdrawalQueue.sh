certoraRun certora/harness/WithdrawalQueueHarness.sol certora/mocks/StETHMock.sol \
    --verify WithdrawalQueueHarness:certora/specs/WithdrawalQueue.spec \
    --link WithdrawalQueueHarness:STETH=StETHMock \
    --optimistic_loop \
    --solc_map WithdrawalQueueHarness=solc8.9,StETHMock=solc4.24 \
    --staging \
    --loop_iter 3 \
    --settings -optimisticFallback=true \
    --msg "WithdrawalQueue - all rules"