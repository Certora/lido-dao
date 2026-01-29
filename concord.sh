gId=$1
# forge install; remove devDependencies from package.json and npm install first
mv package.json package_tmp.json

# Resolve certoraConcord.py path from the certora-cli package
CONCORD_CMD=$(python3 -c "import certora_cli, os; print(os.path.join(os.path.dirname(certora_cli.__file__), 'certoraConcord.py'))" 2>/dev/null)
if [ -z "$CONCORD_CMD" ] || [ ! -f "$CONCORD_CMD" ]; then
    echo "Error: certora-cli package not found. Install it with: pip install certora-cli" >&2
    exit 1
fi

# List of all methods to check
METHODS=(
    "initialize(address,address)"
    "finalizeUpgrade_v3(address,address[],uint256)"
    "pauseStaking()"
    "resumeStaking()"
    "setStakingLimit(uint256,uint256)"
    "removeStakingLimit()"
    "isStakingPaused()"
    "getCurrentStakeLimit()"
    "getStakeLimitFullInfo()"
    "getMaxExternalRatioBP()"
    "setMaxExternalRatioBP(uint256)"
    "receive()"
    "fallback()"
    "submit(address)"
    "receiveELRewards()"
    "receiveWithdrawals()"
    "stop()"
    "resume()"
    "unsafeChangeDepositedValidators(uint256)"
    "getBufferedEther()"
    "getExternalEther()"
    "getExternalShares()"
    "getMaxMintableExternalShares()"
    "getTotalELRewardsCollected()"
    "getLidoLocator()"
    "getBeaconStat()"
    "canDeposit()"
    "getDepositableEther()"
    "deposit(uint256,uint256,bytes)"
    "mintShares(address,uint256)"
    "burnShares(uint256)"
    "mintExternalShares(address,uint256)"
    "burnExternalShares(uint256)"
    "rebalanceExternalEtherToInternal(uint256)"
    "processClStateUpdate(uint256,uint256,uint256,uint256)"
    "internalizeExternalBadDebt(uint256)"
    "collectRewardsAndProcessWithdrawals(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
    "emitTokenRebase(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
    "transferToVault(address)"
    "getWithdrawalCredentials()"
    "getTreasury()"
    "getFee()"
    "getFeeDistribution()"
)

# Iterate over all methods
for method in "${METHODS[@]}"; do
    echo "Checking method: $method"
    python3 "$CONCORD_CMD" contracts/0.4.24/Lido.sol contracts/0.8.25/Lido/LidoNew.sol --check_method "$method" --compiler_map Lido=solc4.24,LidoNew=solc8.25 --server prover --prover_version shelly/equiv --group_id $gId --url_visibility public
done

mv package_tmp.json package.json
