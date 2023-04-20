certoraRun certora/harness/LidoHarness.sol \
    ./contracts/0.8.9/EIP712StETH.sol \
    --verify LidoHarness:certora/specs/Lido_Roy.spec \
    --optimistic_loop \
    --solc_map LidoHarness=solc4.24,EIP712StETH=solc8.9 \
    --cloud pre_cvl2 \
    --loop_iter 3 \
    --rule submitCannotDoSFunctions \
    --settings -optimisticFallback=true \
    --msg "Lido_Roy "