if [[ "$1" ]]
then
    RULE="--rule $1"
fi

if [[ "$2" ]]
then
    MSG="- $2"
fi

certoraRun \
    certora/harnesses/ValidatorsExitBusOracleHarness.sol \
    certora/munged/0.8.9/sanity_checks/OracleReportSanityChecker.sol \
    certora/munged/0.8.9/oracle/HashConsensus.sol \
    --verify ValidatorsExitBusOracleHarness:certora/specs/ValidatorsExitBusOracle.spec \
    --solc solc8.9 \
    --optimistic_loop \
    --loop_iter 3 \
    --rule_sanity \
    --staging pre_cvl2 \
    --send_only \
    --settings -optimisticUnboundedHashing=true \
    $RULE \
    --msg "ValidatorsExitBusOracle: $RULE $MSG"
