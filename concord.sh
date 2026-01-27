gId=$1
# forge install; remove devDependencies from package.json and npm install first
mv package.json package_tmp.json

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
    certoraConcord.py contracts/0.4.24/Lido.sol contracts/0.8.25/Lido/LidoNew.sol --check_method "$method" --solc_map Lido=solc4.24,LidoNew=solc8.25 --server prover --prover_version master --group_id $gId
done

mv package_tmp.json package.json
