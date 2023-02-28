certoraRun \
./contracts/0.8.9/oracle/AccountingOracle.sol \
./contracts/0.8.9/LidoLocator.sol \
./contracts/0.8.9/sanity_checks/OracleReportSanityChecker.sol \
./contracts/0.8.9/StakingRouter.sol \
./contracts/0.8.9/test_helpers/oracle/MockConsensusContract.sol \
./contracts/0.8.9/test_helpers/oracle/MockLidoForAccountingOracle.sol \
./contracts/0.8.9/test_helpers/oracle/MockWithdrawalQueueForAccountingOracle.sol \
./contracts/0.8.9/test_helpers/StakingModuleMock.sol \
./contracts/0.4.24/oracle/LegacyOracle.sol \
\
\
--verify AccountingOracle:certora/specs/AccountingOracle.spec \
\
\
--solc_map AccountingOracle=solc8.9,LidoLocator=solc8.9,\
OracleReportSanityChecker=solc8.9,MockWithdrawalQueueForAccountingOracle=solc8.9,\
StakingRouter=solc8.9,MockConsensusContract=solc8.9,\
MockLidoForAccountingOracle=solc8.9,StakingModuleMock=solc8.9,\
LegacyOracle=solc4.24 \
\
--loop_iter 2 \
--staging yuvalbd/correct_param_count \
--optimistic_loop \
--send_only \
--settings -t=500,-mediumTimeout=50,-copyLoopUnroll=5,-optimisticUnboundedHashing=true \
--rule_sanity \
--msg "with rule_sanity"

# --rule sanity shouldNotRevert \