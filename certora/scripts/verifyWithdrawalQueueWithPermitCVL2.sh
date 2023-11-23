certoraRun  certora/harness/WithdrawalQueueHarness.sol \
            certora/mocks/StETHMock.sol \
            certora/harness/DummyERC20WithPermit.sol \
    --verify WithdrawalQueueHarness:certora/specsCVL2/WithdrawalQueueWithPermit.spec \
    --link  WithdrawalQueueHarness:STETH=StETHMock \
            WithdrawalQueueHarness:WSTETH=DummyERC20WithPermit \
    --optimistic_loop \
    --solc_map WithdrawalQueueHarness=solc8.9,StETHMock=solc4.24,DummyERC20WithPermit=solc8.9 \
    --loop_iter 3 \
    --prover_args '-optimisticFallback true' \
    --server production \
    --msg "cannot front run with permit" \
    --rule cannotFrontRunRequestWithdrawalsWstETHWithPermit