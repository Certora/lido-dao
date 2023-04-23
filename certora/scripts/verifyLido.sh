certoraRun certora/harness/LidoHarness.sol \
    ./contracts/0.8.9/EIP712StETH.sol \
    ./contracts/0.8.9/test_helpers/StakingRouterMockForDepositSecurityModule.sol \
    --verify LidoHarness:certora/specs/Lido_Roy.spec \
    --optimistic_loop \
    --solc_map LidoHarness=solc4.24,EIP712StETH=solc8.9,StakingRouterMockForDepositSecurityModule=solc8.9 \
    --staging pre_cvl2 \
    --send_only \
    --loop_iter 3 \
    --settings -optimisticFallback=true,-contractRecursionLimit=1 \
    --msg "Lido after setup"