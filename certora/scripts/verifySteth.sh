certoraRun certora/mocks/StETHMock.sol \
    --verify StETHMock:certora/specs/StEth.spec \
    --optimistic_loop \
    --solc solc4.24 \
    --staging \
    --loop_iter 3 \
    --settings -optimisticFallback=true \
    --msg "StEth - $1"