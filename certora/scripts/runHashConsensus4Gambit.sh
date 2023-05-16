if [[ "$1" ]]
then
    RULE="--rule $1"
fi

if [[ "$2" ]]
then
    MSG=": $2"
fi

certoraRun \
./contracts/0.8.9/oracle/HashConsensus.sol \
\
--verify HashConsensus:certora/specs/HashConsensus4Gambit.spec \
\
--solc solc8.9 \
\
--loop_iter 2 \
--cloud \
--optimistic_loop \
--settings -t=500,-mediumTimeout=50,-copyLoopUnroll=17,-optimisticUnboundedHashing=true \
--hashing_length_bound 544 \
--rule_sanity \
--debug \
$RULE  \
--msg "$RULE $MSG"