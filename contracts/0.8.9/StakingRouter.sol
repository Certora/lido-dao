// SPDX-FileCopyrightText: 2021 Lido <info@lido.fi>
//
// SPDX-License-Identifier: GPL-3.0
//
pragma solidity 0.8.9;

import "@openzeppelin/contracts-v4.4/access/AccessControlEnumerable.sol";

import "./interfaces/IStakingRouter.sol";
import "./interfaces/IStakingModule.sol";
import "./interfaces/IDepositContract.sol";
import "./lib/BytesLib.sol";
import "./lib/UnstructuredStorage.sol";

import "hardhat/console.sol";

/**
 * @title Interface defining a Lido liquid staking pool
 * @dev see also [Lido liquid staking pool core contract](https://docs.lido.fi/contracts/lido)
 */
interface ILido {
    function totalSupply() external view returns (uint256);

    function getTotalShares() external view returns (uint256);

    function mintShares(uint256 shares2mint) external;

    function transferShares(address recipient, uint256 sharesAmount) external returns (uint256);

    function getWithdrawalCredentials() external view returns (bytes32);

    function updateBufferedCounters(uint256 depositsAmount) external;

    function getTreasury() external view returns (address);

    function getLastReportTimestamp() external view returns (uint64);
}

contract StakingRouter is IStakingRouter, AccessControlEnumerable {
    using UnstructuredStorage for bytes32;

    event ModuleAdded();
    event ModulePaused();
    event ModuleUnpaused();
    event ModuleActiveStatus();
    event DistributedShares(uint256 modulesShares, uint256 treasuryShares, uint256 remainShares);
    event DistributedDeposits(address indexed moduleAddress, uint256 assignedKeys, uint64 timestamp);
    event WithdrawalCredentialsSet(bytes32 withdrawalCredentials);
    event ContractVersionSet(uint256 version);
    /**
      * Emitted when the vault received ETH
      */
    event ETHReceived(uint256 amount);

    struct StakingModule {
        /// @notice name of module
        string name;
        /// @notice address of module
        address moduleAddress;
        /// @notice treasury fee
        uint16 treasuryFee;
        /// @notice target percent of total keys in protocol, in BP
        uint16 targetShare;
        /// @notice flag if module can not accept the deposits
        bool paused;
        /// @notice flag if module can participate in further reward distribution
        bool active;

        uint64 lastDepositAt;

        uint256 lastDepositBlock;
    }

    struct ModuleLookupCacheEntry {
        /// @notice index of module
        uint256 id;
        /// @notice address of module
        address moduleAddress;
        /// @notice total amount of keys in the module
        uint256 totalKeys;
        /// @notice total amount of used keys in the module
        uint256 totalUsedKeys;
        /// @notice total amount of stopped keys in the module
        uint256 totalStoppedKeys;
        /// @notice the number of keys that have been allocated to this module
        uint256 assignedKeys;
        /// @notice treasury fee in BP
        uint16 treasuryFee;
        /// @notice target percent of total keys in protocol, in BP
        uint16 targetShare;
        /// @notice flag if module can not accept the deposits
        bool paused;
        /// @notice flag if module can participate in further reward distribution
        bool active;
        bool skip;
    }

    IDepositContract internal immutable DEPOSIT_CONTRACT;

    bytes32 public constant MANAGE_WITHDRAWAL_KEY_ROLE = keccak256("MANAGE_WITHDRAWAL_KEY_ROLE");
    bytes32 public constant MODULE_PAUSE_ROLE = keccak256("MODULE_PAUSE_ROLE");
    bytes32 public constant MODULE_CONTROL_ROLE = keccak256("MODULE_CONTROL_ROLE");
    bytes32 public constant DEPOSIT_ROLE = keccak256("DEPOSIT_ROLE");

    /// Version of the initialized contract data
    /// NB: Contract versioning starts from 1.
    /// The version stored in CONTRACT_VERSION_POSITION equals to
    /// - 0 right after deployment when no initializer is invoked yet
    /// - N after calling initialize() during deployment from scratch, where N is the current contract version
    /// - N after upgrading contract from the previous version (after calling finalize_vN())
    bytes32 internal constant CONTRACT_VERSION_POSITION = keccak256("lido.StakingRouter.contractVersion");

    /// @dev Credentials which allows the DAO to withdraw Ether on the 2.0 side
    bytes32 internal constant WITHDRAWAL_CREDENTIALS_POSITION = keccak256('lido.StakingRouter.withdrawalCredentials');

    bytes32 internal constant LIDO_POSITION = keccak256('lido.StakingRouter.lido');

    uint256 public constant DEPOSIT_SIZE = 32 ether;

    uint256 internal constant DEPOSIT_AMOUNT_UNIT = 1000000000 wei;
    uint256 internal constant TOTAL_BASIS_POINTS = 10000;

    uint256 public constant PUBKEY_LENGTH = 48;
    uint256 public constant SIGNATURE_LENGTH = 96;

    /// @dev modules amount
    bytes32 internal constant MODULES_COUNT_POSITION = keccak256('lido.StakingRouter.modulesCount');

    /// @dev provisioned total stake = total current stake + total allocation
    bytes32 internal constant TOTAL_ALLOCATION_POSITION = keccak256('lido.StakingRouter.totalAllocation');

    /// @dev last distribute time
    bytes32 internal constant LAST_DISTRIBUTE_AT_POSITION = keccak256('lido.StakingRouter.lastDistributeAt');

    /// @dev last deposits time
    bytes32 internal constant LAST_DEPOSITS_AMOUNT_POSITION = keccak256('lido.StakingRouter.lastDepositsAmount');

    /// CONTRACT STRUCTED STORAGE
    /// @notice SLOT 0: modules map
    mapping(uint256 => StakingModule) internal modules;

    /// @notice SLOT 1: revert map
    mapping(address => uint256) internal modulesIds;

    /// @notice SLOT 2: stake allocation module_index -> amount
    mapping(uint256 => uint256) public allocation;

    constructor(address _depositContract) {
        require(_depositContract != address(0), "DEPOSIT_CONTRACT_ZERO_ADDRESS");

        DEPOSIT_CONTRACT = IDepositContract(_depositContract);
    }

    function initialize(address _lido, address _admin) external {
        require(_lido != address(0), "LIDO_ZERO_ADDRESS");
        require(_admin != address(0), "ADMIN_ZERO_ADDRESS");
        require(CONTRACT_VERSION_POSITION.getStorageUint256() == 0, "BASE_VERSION_MUST_BE_ZERO");

        _setupRole(DEFAULT_ADMIN_ROLE, _admin);

        LIDO_POSITION.setStorageAddress(_lido);
        CONTRACT_VERSION_POSITION.setStorageUint256(1);
        emit ContractVersionSet(1);
    }

    receive() external payable {
        emit ETHReceived(msg.value);
    }

    /**
     * @notice register a new module
     * @param _name name of module
     * @param _moduleAddress target percent of total keys in protocol, in BP
     * @param _targetShare target total stake share
     * @param _treasuryFee treasury fee
     */
    function addModule(string memory _name, address _moduleAddress, uint16 _targetShare, uint16 _treasuryFee)
        external
        onlyRole(MODULE_PAUSE_ROLE)
    {
        require(_targetShare <= TOTAL_BASIS_POINTS, "VALUE_OVER_100_PERCENT");
        require(_treasuryFee <= TOTAL_BASIS_POINTS, "VALUE_OVER_100_PERCENT");

        uint256 _modulesCount = getModulesCount();
        StakingModule storage module = modules[_modulesCount];
        modulesIds[_moduleAddress] = _modulesCount;

        module.name = _name;
        module.moduleAddress = _moduleAddress;
        module.targetShare = _targetShare;
        module.treasuryFee = _treasuryFee;
        module.paused = false;
        module.active = true;

        MODULES_COUNT_POSITION.setStorageUint256(++_modulesCount);
        //@todo call distribute ?
    }

    function getModule(uint256 moduleId) external view returns (StakingModule memory) {
        //@todo check exists

        return modules[moduleId];
    }

    /**
     * @notice Returns total number of node operators
     */
    function getModulesCount() public view returns (uint256) {
        return MODULES_COUNT_POSITION.getStorageUint256();
    }

    /**
     * @notice pause deposits for module
     * @param stakingModule address of module
     */
    function pauseStakingModule(address stakingModule) external onlyRole(MODULE_PAUSE_ROLE) {
        StakingModule storage module = _getModuleByAddress(stakingModule);
        require(!module.paused, "module_is_paused");

        module.paused = true;
    }

    /**
     * @notice unpause deposits for module
     * @param stakingModule address of module
     */
    function unpauseStakingModule(address stakingModule) external onlyRole(MODULE_CONTROL_ROLE) {
        StakingModule storage module = _getModuleByAddress(stakingModule);
        if (module.paused) {
            module.paused = false;
        }
    }

    /**
     * @notice set the module activity flag for participation in further reward distribution
     */
    function setStakingModuleActive(address stakingModule, bool _active) external onlyRole(MODULE_CONTROL_ROLE) {
        StakingModule storage module = _getModuleByAddress(stakingModule);
        module.active = _active;
    }

    function getStakingModuleIsPaused(address stakingModule) external view returns (bool) {
        StakingModule storage module = _getModuleByAddress(stakingModule);
        return module.paused;
    }

    function getStakingModuleKeysOpIndex(address stakingModule) external view returns (uint256) {
        return IStakingModule(stakingModule).getKeysOpIndex();
    }

    function getStakingModuleLastDepositBlock(address stakingModule) external view returns (uint256) {
        StakingModule storage module = _getModuleByAddress(stakingModule);
        return module.lastDepositBlock;
    }

    function _getModuleByAddress(address _moduleAddress) internal view returns(StakingModule storage) {
        uint256 _moduleIndex = modulesIds[_moduleAddress];
        StakingModule storage module = modules[_moduleIndex];
        return module;
    }

    /**
     * @notice get total keys which can used for rewards and center distribution
     *         active keys = used keys - stopped keys
     *
     * @return totalActiveKeys total keys which used for calculation
     * @return moduleActiveKeys array of amount module keys
     */
    function getTotalActiveKeys() public view returns (uint256 totalActiveKeys, uint256[] memory moduleActiveKeys) {
        // calculate total used keys for operators
        uint256 _modulesCount = getModulesCount();
        moduleActiveKeys = new uint256[](_modulesCount);
        for (uint256 i = 0; i < _modulesCount; ++i) {
            StakingModule memory stakingModule = modules[i];
            IStakingModule module = IStakingModule(stakingModule.moduleAddress);
            moduleActiveKeys[i] = module.getTotalUsedKeys() - module.getTotalStoppedKeys();
            totalActiveKeys += moduleActiveKeys[i];
        }
    }

    /**
     * @notice return shares table
     *
     * @return recipients recipients list
     * @return modulesShares shares of each recipient
     * @return moduleFee shares of each recipient
     * @return treasuryFee shares of each recipient
     */
    function getSharesTable()
        external
        view
        returns (address[] memory recipients, uint256[] memory modulesShares, uint256[] memory moduleFee, uint256[] memory treasuryFee)
    {
        uint256 _modulesCount = getModulesCount();
        assert(_modulesCount != 0);

        // +1 for treasury
        recipients = new address[](_modulesCount);
        modulesShares = new uint256[](_modulesCount);
        moduleFee = new uint256[](_modulesCount);
        treasuryFee = new uint256[](_modulesCount);

        uint256 idx = 0;
        uint256 treasuryShares = 0;

        (uint256 totalActiveKeys, uint256[] memory moduleActiveKeys) = getTotalActiveKeys();

        require(totalActiveKeys > 0, "NO_KEYS");

        for (uint256 i = 0; i < _modulesCount; ++i) {
            StakingModule memory stakingModule = modules[i];
            IStakingModule module = IStakingModule(stakingModule.moduleAddress);

            recipients[idx] = stakingModule.moduleAddress;
            modulesShares[idx] = (moduleActiveKeys[i] * TOTAL_BASIS_POINTS / totalActiveKeys);
            moduleFee[idx] = module.getFee();
            treasuryFee[idx] = stakingModule.treasuryFee;

            ++idx;
        }

        return (recipients, modulesShares, moduleFee, treasuryFee);
    }

    function distributeDeposits() public {
        uint256 depositsAmount = address(this).balance / DEPOSIT_SIZE;

        (ModuleLookupCacheEntry[] memory cache, uint256 newTotalAllocation) = getAllocation(depositsAmount);

        uint256 _modulesCount = getModulesCount();
        uint64 _now = uint64(block.timestamp);
        bool isUpdated;

        for (uint256 i = 0; i < _modulesCount; i++) {
            if (allocation[i] != cache[i].assignedKeys) {
                allocation[i] = cache[i].assignedKeys;
                isUpdated = true;
                if (cache[i].assignedKeys > 0) {
                    emit DistributedDeposits(cache[i].moduleAddress, cache[i].assignedKeys, _now);
                }
            }
        }
        // @todo придумать более красивый способ от повторного распределения
        // кейс:
        // - предположим, у нас 3 модуля:
        //   1. Curated: totalKeys = 15000, totalUsedKeys = 9700, targetShare = 100% (т.е. без ограничений)
        //   2. Community: totalKeys = 300, totalUsedKeys = 100, targetShare = 1% (1% от общего числа валидаторов)
        //   3. DVT:  totalKeys = 200, totalUsedKeys = 0, targetShare = 5% (5% от общего числа валидаторов)
        // - на баланс SR приходит eth на 200 депозитов и вызывается distributeDeposits
        // - происходит аллокация по модулям (targetShare модулей в данном случае не превышен),
        //  тогда депозиты(ключи) распределятся так: Curated - 0, Community - 50, DVT - 150. Таблица аллокации: [0, 50, 150]
        // - допустим в тчении 12 часов Community и Curated модули функционируют нормально, а DVT модуль тормозит.
        // - Если Community модуль уже задепозитил 10 из своих ключей, значит вся его аллокация (т.е.
        //   еще 40 незадепозиченных ключей) не попадает под механизм recycle, а 100% аллокации DVT модуля
        //   становится доступна для депозита другими модулями.
        // - допустим Curated модуль через 12 часов депозитит все доступные recycled ключи: 100% от 150 ключей DVT модуля.
        //   Новая таблица аллокаци после депозита: [0, 40, 0].
        // - допустим, на SR приходит еще eth на 1 депозит, и повторно вывзывается distributeDeposits: метод отработает и
        //   переформирует таблицу аллокаций на: [0, 0, 40] - и ключи модуля 1 снова становятся доступны для депозита любым
        //   модулем, т.к. перетекли в корзинку модуля DVT, который на данный момент уже числится "тормозным"
        //
        // suggested solution: close the call distributeDeposits() wuth security role



        require(depositsAmount > getLastDepositsAmount() && isUpdated, "allocation not changed");
        TOTAL_ALLOCATION_POSITION.setStorageUint256(newTotalAllocation);
        LAST_DISTRIBUTE_AT_POSITION.setStorageUint256(_now);
        LAST_DEPOSITS_AMOUNT_POSITION.setStorageUint256(depositsAmount);
    }

    /**
     * @dev This function returns the allocation table of the specified number of keys (deposits) between modules, depending on restrictions/pauses.
     *      Priority is given to models with the lowest number of used keys
     * @param keysToDistribute the number of keys to distribute between modules
     * @return cache modules with assignedKeys variable which store the number of keys allocation
     */
    function getAllocation(uint256 keysToDistribute)
        public
        view
        returns (ModuleLookupCacheEntry[] memory cache, uint256 newTotalAllocation)
    {
        uint256 curTotalAllocation;
        (cache, curTotalAllocation) = _loadModuleCache();

        ModuleLookupCacheEntry memory entry;
        uint256 _modulesCount = getModulesCount();

        uint256 distributedKeys;
        uint256 bestModuleIdx;
        uint256 smallestStake;
        uint256 stake;
        newTotalAllocation = curTotalAllocation + keysToDistribute;
        while (distributedKeys < keysToDistribute) {
            bestModuleIdx = _modulesCount;
            smallestStake = 0;

            for (uint256 i = 0; i < _modulesCount; i++) {
                entry = cache[i];
                if (entry.skip) {
                    continue;
                }

                unchecked {
                    stake = entry.totalUsedKeys + entry.assignedKeys - entry.totalStoppedKeys;
                }
                if (
                    entry.totalUsedKeys + entry.assignedKeys == entry.totalKeys || entry.targetShare == 0
                        || (entry.targetShare < 10000 && stake >= (newTotalAllocation * entry.targetShare) / TOTAL_BASIS_POINTS)
                ) {
                    cache[i].skip = true;
                    continue;
                }

                if (bestModuleIdx == _modulesCount || stake < smallestStake) {
                    bestModuleIdx = i;
                    smallestStake = stake;
                }
            }

            if (bestModuleIdx == _modulesCount) {
                // not found
                break;
            }

            unchecked {
                cache[bestModuleIdx].assignedKeys++;
                distributedKeys++;
            }
        }

        require(distributedKeys > 0, "INVALID_ASSIGNED_KEYS");

        // get new provisoned total stake
        newTotalAllocation = curTotalAllocation + distributedKeys;
    }

    function getLastReportTimestamp() public view returns (uint64 lastReportAt) {
        address lido = getLido();
        return ILido(lido).getLastReportTimestamp();
    }

    function getLido() public view returns (address) {
        return LIDO_POSITION.getStorageAddress();
    }

    function _loadModuleCache() internal view returns (ModuleLookupCacheEntry[] memory cache, uint256 newTotalAllocation) {
        uint256 _modulesCount = getModulesCount();
        cache = new ModuleLookupCacheEntry[](_modulesCount);
        if (0 == cache.length) return (cache, 0);

        uint256 idx = 0;
        for (uint256 i = 0; i < _modulesCount; ++i) {
            StakingModule memory stakingModule = modules[i];
            IStakingModule module = IStakingModule(stakingModule.moduleAddress);

            ModuleLookupCacheEntry memory entry = cache[idx++];
            entry.id = i;
            entry.moduleAddress = stakingModule.moduleAddress;
            entry.totalKeys = module.getTotalKeys();
            entry.totalUsedKeys = module.getTotalUsedKeys();
            entry.totalStoppedKeys = module.getTotalStoppedKeys();
            entry.targetShare = stakingModule.targetShare;
            entry.paused = stakingModule.paused;
            // prefill skip flag for paused or full modules
            entry.skip = entry.paused || entry.totalUsedKeys == entry.totalKeys;
            // update global totals
            newTotalAllocation += (entry.totalUsedKeys - entry.totalStoppedKeys);
        }
    }

    /**
     * @dev Invokes a deposit call to the official Deposit contract
     * @param maxDepositsCount max deposits count
     * @param stakingModule module address
     * @param depositCalldata module calldata
     */
    function deposit(uint256 maxDepositsCount, address stakingModule, bytes calldata depositCalldata) 
        external 
        onlyRole(DEPOSIT_ROLE) 
    {
        uint256 moduleId = modulesIds[stakingModule];
        uint256 allocatedKeys = allocation[moduleId];
        uint256 numKeys = allocatedKeys < maxDepositsCount ? allocatedKeys : maxDepositsCount;

        require(numKeys > 0, "EMPTY_ALLOCATION");

        IStakingModule module = IStakingModule(stakingModule);
        (bytes memory pubkeys, bytes memory signatures) = module.prepNextSigningKeys(numKeys, depositCalldata);

        //bytes memory pubkeys, bytes memory signatures
        require(pubkeys.length > 0, "INVALID_PUBKEYS");

        require(pubkeys.length % PUBKEY_LENGTH == 0, "REGISTRY_INCONSISTENT_PUBKEYS_LEN");
        require(signatures.length % SIGNATURE_LENGTH == 0, "REGISTRY_INCONSISTENT_SIG_LEN");

        uint256 depositsCount = pubkeys.length / PUBKEY_LENGTH;
        require(depositsCount == signatures.length / SIGNATURE_LENGTH, "REGISTRY_INCONSISTENT_SIG_COUNT");

        require(modules[moduleId].active && !modules[moduleId].paused, "module paused or not active");

        for (uint256 i = 0; i < depositsCount; ++i) {
            bytes memory pubkey = BytesLib.slice(pubkeys, i * PUBKEY_LENGTH, PUBKEY_LENGTH);
            bytes memory signature = BytesLib.slice(signatures, i * SIGNATURE_LENGTH, SIGNATURE_LENGTH);
            _stake(pubkey, signature);
        }

        allocation[moduleId] -= depositsCount;
        address lido = getLido();
        ILido(lido).updateBufferedCounters(depositsCount);

        modules[moduleId].lastDepositAt = uint64(block.timestamp);
        modules[moduleId].lastDepositBlock = block.number;

        // reduce rest amount of deposits
        LAST_DEPOSITS_AMOUNT_POSITION.setStorageUint256(getLastDepositsAmount() - depositsCount);
    }

    /**
     * @dev Invokes a deposit call to the official Deposit contract
     * @param _pubkey Validator to stake for
     * @param _signature Signature of the deposit call
     */
    function _stake(bytes memory _pubkey, bytes memory _signature) internal {
        bytes32 withdrawalCredentials = getWithdrawalCredentials();
        require(withdrawalCredentials != 0, "EMPTY_WITHDRAWAL_CREDENTIALS");

        uint256 value = DEPOSIT_SIZE;

        // The following computations and Merkle tree-ization will make official Deposit contract happy
        uint256 depositsAmount = value / DEPOSIT_AMOUNT_UNIT;
        assert(depositsAmount * DEPOSIT_AMOUNT_UNIT == value); // properly rounded

        // Compute deposit data root (`DepositData` hash tree root) according to deposit_contract.sol
        bytes32 pubkeyRoot = sha256(_pad64(_pubkey));
        bytes32 signatureRoot = sha256(
            abi.encodePacked(
                sha256(BytesLib.slice(_signature, 0, 64)), sha256(_pad64(BytesLib.slice(_signature, 64, SIGNATURE_LENGTH - 64)))
            )
        );

        bytes32 depositDataRoot = sha256(
            abi.encodePacked(
                sha256(abi.encodePacked(pubkeyRoot, withdrawalCredentials)),
                sha256(abi.encodePacked(_toLittleEndian64(depositsAmount), signatureRoot))
            )
        );

        uint256 targetBalance = address(this).balance - value;

        getDepositContract().deposit{value: value}(_pubkey, abi.encodePacked(withdrawalCredentials), _signature, depositDataRoot);
        require(address(this).balance == targetBalance, "EXPECTING_DEPOSIT_TO_HAPPEN");
    }

    function _trimUnusedKeys() internal {
        uint256 _modulesCount = getModulesCount();
        if (_modulesCount > 0) {
            for (uint256 i = 0; i < _modulesCount; ++i) {
                StakingModule memory stakingModule = modules[i];
                IStakingModule module = IStakingModule(stakingModule.moduleAddress);

                module.trimUnusedKeys();
            }
        }
    }

    /**
     * @notice Gets deposit contract handle
     */
    function getDepositContract() public view returns (IDepositContract) {
        return DEPOSIT_CONTRACT;
    }

    /**
     * @dev Padding memory array with zeroes up to 64 bytes on the right
     * @param _b Memory array of size 32 .. 64
     */
    function _pad64(bytes memory _b) internal pure returns (bytes memory) {
        assert(_b.length >= 32 && _b.length <= 64);
        if (64 == _b.length) return _b;

        bytes memory zero32 = new bytes(32);
        assembly {
            mstore(add(zero32, 0x20), 0)
        }

        if (32 == _b.length) return BytesLib.concat(_b, zero32);
        else return BytesLib.concat(_b, BytesLib.slice(zero32, 0, uint256(64) - _b.length));
    }

    /**
     * @dev Converting value to little endian bytes and padding up to 32 bytes on the right
     * @param _value Number less than `2**64` for compatibility reasons
     */
    function _toLittleEndian64(uint256 _value) internal pure returns (uint256 result) {
        result = 0;
        uint256 temp_value = _value;
        for (uint256 i = 0; i < 8; ++i) {
            result = (result << 8) | (temp_value & 0xFF);
            temp_value >>= 8;
        }

        assert(0 == temp_value); // fully converted
        result <<= (24 * 8);
    }

    /**
     * @notice Set credentials to withdraw ETH on ETH 2.0 side after the phase 2 is launched to `_withdrawalCredentials`
     * @dev Note that setWithdrawalCredentials discards all unused signing keys as the signatures are invalidated.
     * @param _withdrawalCredentials withdrawal credentials field as defined in the Ethereum PoS consensus specs
     */
    function setWithdrawalCredentials(bytes32 _withdrawalCredentials) external onlyRole(MANAGE_WITHDRAWAL_KEY_ROLE) {

        WITHDRAWAL_CREDENTIALS_POSITION.setStorageBytes32(_withdrawalCredentials);

        //trim keys with old WC
        _trimUnusedKeys();

        emit WithdrawalCredentialsSet(_withdrawalCredentials);
    }

    /**
     * @notice Returns current credentials to withdraw ETH on ETH 2.0 side after the phase 2 is launched
     */
    function getWithdrawalCredentials() public view returns (bytes32) {
        return WITHDRAWAL_CREDENTIALS_POSITION.getStorageBytes32();
    }

    function getTotalAllocation() public view returns(uint256) {
        return TOTAL_ALLOCATION_POSITION.getStorageUint256();
    }

    function getLastDistributeAt() public view returns(uint64) {
        return uint64(LAST_DISTRIBUTE_AT_POSITION.getStorageUint256());
    }

    function getLastDepositsAmount() public view returns(uint256) {
        return LAST_DEPOSITS_AMOUNT_POSITION.getStorageUint256();    
    }
}
