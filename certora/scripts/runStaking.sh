if [[ "$1" ]]
then
    RULE="--rule $1"
fi

certoraRun certora/harness/StakingRouterHarness.sol:StakingRouter \
    --verify StakingRouter:certora/specs/staking_router.spec \
    $RULE \
    --solc solc8.10 \
    --optimistic_loop \
    --send_only \
    --msg "Lido: StakingRouter $1"
# --sanity
 