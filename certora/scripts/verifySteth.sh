certoraRun contracts/0.4.24/Lido.sol \
    --verify Lido:certora/specs/StEth.spec \
    --optimistic_loop \
    --solc solc4.24 \
    --staging \
    --loop_iter 3 \
    --settings -optimisticFallback=true \
    --msg "StEth - noFeeOnTransferFrom" --rule noFeeOnTransferFrom