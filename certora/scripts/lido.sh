certoraRun certora/harness/LidoHarness.sol \
    contracts/0.8.9/sanity_checks/OracleReportSanityChecker.sol \
    contracts/0.8.9/LidoExecutionLayerRewardsVault.sol \
    contracts/0.8.9/WithdrawalVault.sol  \
    contracts/0.8.9/Burner.sol \
    --verify LidoHarness:certora/specs/lido.spec \
    --optimistic_loop \
    --solc_map LidoHarness=solc4.24,OracleReportSanityChecker=solc8.9,Burner=solc8.9,LidoExecutionLayerRewardsVault=solc8.9,WithdrawalVault=solc8.9\
    --staging \
    --loop_iter 3 \
    --settings -t=4000,-mediumTimeout=100,-depth=16 \
    --send_only