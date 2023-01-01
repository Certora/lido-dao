if [[ "$1" ]]
then
    RULE="--rule $1"
fi

certoraRun certora/harness/StakingRouterHarness.sol:StakingRouter \
    --verify StakingRouter:certora/specs/staking_router.spec \
    $RULE \
    --solc solc8.9 \
    --optimistic_loop \
    --staging master \
    --send_only \
    --msg "Lido: StakingRouter $1"
# --sanity
 