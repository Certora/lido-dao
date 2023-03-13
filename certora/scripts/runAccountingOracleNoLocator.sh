if [[ "$1" ]]
then
    RULE="--rule $1"
fi

if [[ "$2" ]]
then
    MSG=": $2"
fi

certoraRun \
./contracts/0.8.9/oracle/AccountingOracle.sol \
./contracts/0.8.9/sanity_checks/OracleReportSanityChecker.sol \
./contracts/0.8.9/StakingRouter.sol \
./contracts/0.8.9/test_helpers/oracle/MockConsensusContract.sol \
./contracts/0.8.9/test_helpers/oracle/MockLidoForAccountingOracle.sol \
./contracts/0.8.9/test_helpers/oracle/MockWithdrawalQueueForAccountingOracle.sol \
./contracts/0.8.9/test_helpers/StakingModuleMock.sol \
./contracts/0.4.24/oracle/LegacyOracle.sol \
\
--verify AccountingOracle:certora/specs/AccountingOracle.spec \
\
--link AccountingOracle:LIDO=MockLidoForAccountingOracle \
AccountingOracle:LEGACY_ORACLE=LegacyOracle \
\
--solc_map AccountingOracle=solc8.9,\
OracleReportSanityChecker=solc8.9,MockWithdrawalQueueForAccountingOracle=solc8.9,\
StakingRouter=solc8.9,MockConsensusContract=solc8.9,\
MockLidoForAccountingOracle=solc8.9,StakingModuleMock=solc8.9,\
LegacyOracle=solc4.24 \
\
--loop_iter 2 \
--staging master \
--optimistic_loop \
--send_only \
--settings -t=500,-mediumTimeout=50,-copyLoopUnroll=17,-optimisticUnboundedHashing=true \
--hashing_length_bound 544 \
--rule_sanity \
--debug \
$RULE  \
--msg "$RULE $MSG" \
# \
# --rule correctCountOnRenounceRole correctCountOnGrantRole memberCountNonInterference \
# --msg "correctCountOnRenounceRole correctCountOnGrantRole with ensure, memberCountNonInterference"
# --msg "all rules: require contractAddressesLinked, comment out AddressCannotBeSame in BaseOracle.sol"
# --msg "all rules with require on contractAddressesLinked"
# --msg "all rules, not commented AddressCannotBeSame" \
# ./contracts/0.8.9/LidoLocator.sol \
# --link AccountingOracle:LOCATOR=LidoLocator \
# --solc_map AccountingOracle=solc8.9,LidoLocator=solc8.9,\
# --staging yuvalbd/correct_param_count \