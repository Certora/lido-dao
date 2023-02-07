// SPDX-FileCopyrightText: 2023 Lido <info@lido.fi>

// SPDX-License-Identifier: GPL-3.0

/* See contracts/COMPILERS.md */
pragma solidity 0.8.9;

import {AccessControlEnumerable} from "./utils/access/AccessControlEnumerable.sol";

import {IStakingModule} from "./interfaces/IStakingModule.sol";

import {Math256} from "../common/lib/Math256.sol";
import {UnstructuredStorage} from "./lib/UnstructuredStorage.sol";
import {MinFirstAllocationStrategy} from "../common/lib/MinFirstAllocationStrategy.sol";

import {BeaconChainDepositor} from "./BeaconChainDepositor.sol";
import {Versioned} from "./utils/Versioned.sol";

interface ILido {
    function getBufferedEther() external view returns (uint256);
    function receiveStakingRouterDepositRemainder() external payable;
}

contract StakingRouter is AccessControlEnumerable, BeaconChainDepositor, Versioned {
    using UnstructuredStorage for bytes32;

    /// @dev events
    event StakingModuleAdded(uint24 indexed stakingModuleId, address stakingModule, string name, address createdBy);
    event StakingModuleTargetShareSet(uint24 indexed stakingModuleId, uint16 targetShare, address setBy);
    event StakingModuleFeesSet(uint24 indexed stakingModuleId, uint16 stakingModuleFee, uint16 treasuryFee, address setBy);
    event StakingModuleStatusSet(uint24 indexed stakingModuleId, StakingModuleStatus status, address setBy);
    event StakingModuleExitedKeysIncompleteReporting(uint24 indexed stakingModuleId, uint256 unreportedExitedKeysCount);
    event WithdrawalCredentialsSet(bytes32 withdrawalCredentials, address setBy);
    /**
     * Emitted when the StakingRouter received ETH
     */
    event StakingRouterETHDeposited(uint24 indexed stakingModuleId, uint256 amount);

    /// @dev errors
    error ErrorZeroAddress(string field);
    error ErrorValueOver100Percent(string field);
    error ErrorStakingModuleNotActive();
    error ErrorStakingModuleNotPaused();
    error ErrorEmptyWithdrawalsCredentials();
    error ErrorDirectETHTransfer();
    error ErrorExitedKeysCountCannotDecrease();
    error ErrorStakingModulesLimitExceeded();
    error ErrorStakingModuleIdTooLarge();
    error ErrorStakingModuleUnregistered();
    error ErrorAppAuthLidoFailed();
    error ErrorStakingModuleStatusTheSame();
    error ErrorStakingModuleWrongName();
    error UnexpectedCurrentKeysCount(
        uint256 currentModuleExitedKeysCount,
        uint256 currentNodeOpExitedKeysCount,
        uint256 currentNodeOpStuckKeysCount
    );

    enum StakingModuleStatus {
        Active, // deposits and rewards allowed
        DepositsPaused, // deposits NOT allowed, rewards allowed
        Stopped // deposits and rewards NOT allowed
    }

    struct StakingModule {
        /// @notice unique id of the staking module
        uint24 id;
        /// @notice address of staking module
        address stakingModuleAddress;
        /// @notice part of the fee taken from staking rewards that goes to the staking module
        uint16 stakingModuleFee;
        /// @notice part of the fee taken from staking rewards that goes to the treasury
        uint16 treasuryFee;
        /// @notice target percent of total keys in protocol, in BP
        uint16 targetShare;
        /// @notice staking module status if staking module can not accept the deposits or can participate in further reward distribution
        uint8 status;
        /// @notice name of staking module
        string name;
        /// @notice block.timestamp of the last deposit of the staking module
        uint64 lastDepositAt;
        /// @notice block.number of the last deposit of the staking module
        uint256 lastDepositBlock;
        /// @notice number of exited keys
        uint256 exitedKeysCount;
    }

    struct StakingModuleCache {
        address stakingModuleAddress;
        uint24 stakingModuleId;
        uint16 stakingModuleFee;
        uint16 treasuryFee;
        uint16 targetShare;
        StakingModuleStatus status;
        uint256 activeKeysCount;
        uint256 availableKeysCount;
    }

    bytes32 public constant MANAGE_WITHDRAWAL_CREDENTIALS_ROLE = keccak256("MANAGE_WITHDRAWAL_CREDENTIALS_ROLE");
    bytes32 public constant STAKING_MODULE_PAUSE_ROLE = keccak256("STAKING_MODULE_PAUSE_ROLE");
    bytes32 public constant STAKING_MODULE_RESUME_ROLE = keccak256("STAKING_MODULE_RESUME_ROLE");
    bytes32 public constant STAKING_MODULE_MANAGE_ROLE = keccak256("STAKING_MODULE_MANAGE_ROLE");
    bytes32 public constant REPORT_EXITED_KEYS_ROLE = keccak256("REPORT_EXITED_KEYS_ROLE");
    bytes32 public constant UNSAFE_SET_EXITED_KEYS_ROLE = keccak256("UNSAFE_SET_EXITED_KEYS_ROLE");
    bytes32 public constant REPORT_REWARDS_MINTED_ROLE = keccak256("REPORT_REWARDS_MINTED_ROLE");

    bytes32 internal constant LIDO_POSITION = keccak256("lido.StakingRouter.lido");

    /// @dev Credentials which allows the DAO to withdraw Ether on the 2.0 side
    bytes32 internal constant WITHDRAWAL_CREDENTIALS_POSITION = keccak256("lido.StakingRouter.withdrawalCredentials");

    /// @dev total count of staking modules
    bytes32 internal constant STAKING_MODULES_COUNT_POSITION = keccak256("lido.StakingRouter.stakingModulesCount");
    /// @dev id of the last added staking module. This counter grow on staking modules adding
    bytes32 internal constant LAST_STAKING_MODULE_ID_POSITION = keccak256("lido.StakingRouter.lastStakingModuleId");
    /// @dev mapping is used instead of array to allow to extend the StakingModule
    bytes32 internal constant STAKING_MODULES_MAPPING_POSITION = keccak256("lido.StakingRouter.stakingModules");
    /// @dev Position of the staking modules in the `_stakingModules` map, plus 1 because
    ///      index 0 means a value is not in the set.
    bytes32 internal constant STAKING_MODULE_INDICES_MAPPING_POSITION = keccak256("lido.StakingRouter.stakingModuleIndicesOneBased");

    uint256 public constant FEE_PRECISION_POINTS = 10 ** 20; // 100 * 10 ** 18
    uint256 public constant TOTAL_BASIS_POINTS = 10000;

    uint256 internal constant UINT24_MAX = type(uint24).max;

    modifier validStakingModuleId(uint256 _stakingModuleId) {
        if (_stakingModuleId > UINT24_MAX) revert ErrorStakingModuleIdTooLarge();
        _;
    }

    constructor(address _depositContract) BeaconChainDepositor(_depositContract) {}

    /**
     * @dev proxy initialization
     * @param _admin Lido DAO Aragon agent contract address
     * @param _lido Lido address
     * @param _withdrawalCredentials Lido withdrawal vault contract address
     */
    function initialize(address _admin, address _lido, bytes32 _withdrawalCredentials) external {
        if (_admin == address(0)) revert ErrorZeroAddress("_admin");
        if (_lido == address(0)) revert ErrorZeroAddress("_lido");

        _initializeContractVersionTo(1);

        _setupRole(DEFAULT_ADMIN_ROLE, _admin);

        LIDO_POSITION.setStorageAddress(_lido);
        WITHDRAWAL_CREDENTIALS_POSITION.setStorageBytes32(_withdrawalCredentials);
        emit WithdrawalCredentialsSet(_withdrawalCredentials, msg.sender);
    }

    /// @dev prohibit direct transfer to contract
    receive() external payable {
        revert ErrorDirectETHTransfer();
    }

    /**
     * @notice Return the Lido contract address
     */
    function getLido() public view returns (ILido) {
        return ILido(LIDO_POSITION.getStorageAddress());
    }

    /**
     * @notice register a new staking module
     * @param _name name of staking module
     * @param _stakingModuleAddress address of staking module
     * @param _targetShare target total stake share
     * @param _stakingModuleFee fee of the staking module taken from the consensus layer rewards
     * @param _treasuryFee treasury fee
     */
    function addStakingModule(
        string calldata _name,
        address _stakingModuleAddress,
        uint16 _targetShare,
        uint16 _stakingModuleFee,
        uint16 _treasuryFee
    ) external onlyRole(STAKING_MODULE_MANAGE_ROLE) {
        if (_targetShare > TOTAL_BASIS_POINTS) revert ErrorValueOver100Percent("_targetShare");
        if (_stakingModuleFee + _treasuryFee > TOTAL_BASIS_POINTS) revert ErrorValueOver100Percent("_stakingModuleFee + _treasuryFee");
        if (_stakingModuleAddress == address(0)) revert ErrorZeroAddress("_stakingModuleAddress");
        if (bytes(_name).length == 0 || bytes(_name).length > 32) revert ErrorStakingModuleWrongName();

        uint256 newStakingModuleIndex = getStakingModulesCount();

        if (newStakingModuleIndex >= 32) revert ErrorStakingModulesLimitExceeded();
        StakingModule storage newStakingModule = _getStakingModuleByIndex(newStakingModuleIndex);
        uint24 newStakingModuleId = uint24(LAST_STAKING_MODULE_ID_POSITION.getStorageUint256()) + 1;

        newStakingModule.id = newStakingModuleId;
        newStakingModule.name = _name;
        newStakingModule.stakingModuleAddress = _stakingModuleAddress;
        newStakingModule.targetShare = _targetShare;
        newStakingModule.stakingModuleFee = _stakingModuleFee;
        newStakingModule.treasuryFee = _treasuryFee;
        /// @dev since `enum` is `uint8` by nature, so the `status` is stored as `uint8` to avoid possible problems when upgrading.
        ///      But for human readability, we use `enum` as function parameter type.
        ///      More about conversion in the docs https://docs.soliditylang.org/en/v0.8.17/types.html#enums
        newStakingModule.status = uint8(StakingModuleStatus.Active);

        _setStakingModuleIndexById(newStakingModuleId, newStakingModuleIndex);
        LAST_STAKING_MODULE_ID_POSITION.setStorageUint256(newStakingModuleId);
        STAKING_MODULES_COUNT_POSITION.setStorageUint256(newStakingModuleIndex + 1);

        emit StakingModuleAdded(newStakingModuleId, _stakingModuleAddress, _name, msg.sender);
        emit StakingModuleTargetShareSet(newStakingModuleId, _targetShare, msg.sender);
        emit StakingModuleFeesSet(newStakingModuleId, _stakingModuleFee, _treasuryFee, msg.sender);
    }

    /**
     * @notice Update staking module params
     * @param _stakingModuleId staking module id
     * @param _targetShare target total stake share
     * @param _stakingModuleFee fee of the staking module taken from the consensus layer rewards
     * @param _treasuryFee treasury fee
     */
    function updateStakingModule(
        uint256 _stakingModuleId,
        uint16 _targetShare,
        uint16 _stakingModuleFee,
        uint16 _treasuryFee
    ) external
      validStakingModuleId(_stakingModuleId)
      onlyRole(STAKING_MODULE_MANAGE_ROLE)
    {
        if (_targetShare > TOTAL_BASIS_POINTS) revert ErrorValueOver100Percent("_targetShare");
        if (_stakingModuleFee + _treasuryFee > TOTAL_BASIS_POINTS) revert ErrorValueOver100Percent("_stakingModuleFee + _treasuryFee");

        uint256 stakingModuleIndex = _getStakingModuleIndexById(_stakingModuleId);
        StakingModule storage stakingModule = _getStakingModuleByIndex(stakingModuleIndex);

        stakingModule.targetShare = _targetShare;
        stakingModule.treasuryFee = _treasuryFee;
        stakingModule.stakingModuleFee = _stakingModuleFee;

        emit StakingModuleTargetShareSet(uint24(_stakingModuleId), _targetShare, msg.sender);
        emit StakingModuleFeesSet(uint24(_stakingModuleId), _stakingModuleFee, _treasuryFee, msg.sender);
    }

    function reportRewardsMinted(uint256[] calldata _stakingModuleIds, uint256[] calldata _totalShares)
        external
        onlyRole(REPORT_REWARDS_MINTED_ROLE)
    {
        for (uint256 i = 0; i < _stakingModuleIds.length; ) {
            address moduleAddr = _getStakingModuleById(_stakingModuleIds[i]).stakingModuleAddress;
            IStakingModule(moduleAddr).handleRewardsMinted(_totalShares[i]);
            unchecked { ++i; }
        }
    }

    function updateExitedKeysCountByStakingModule(
        uint256[] calldata _stakingModuleIds,
        uint256[] calldata _exitedKeysCounts
    )
        external
        onlyRole(REPORT_EXITED_KEYS_ROLE)
    {
        for (uint256 i = 0; i < _stakingModuleIds.length; ) {
            StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleIds[i]);
            uint256 prevReportedExitedKeysCount = stakingModule.exitedKeysCount;
            if (_exitedKeysCounts[i] < prevReportedExitedKeysCount) {
                revert ErrorExitedKeysCountCannotDecrease();
            }
            (uint256 moduleExitedKeysCount,,) = IStakingModule(stakingModule.stakingModuleAddress)
                .getValidatorsKeysStats();
            if (moduleExitedKeysCount < prevReportedExitedKeysCount) {
                // not all of the exited keys were async reported to the module
                emit StakingModuleExitedKeysIncompleteReporting(
                    stakingModule.id,
                    prevReportedExitedKeysCount - moduleExitedKeysCount
                );
            }
            stakingModule.exitedKeysCount = _exitedKeysCounts[i];
            unchecked { ++i; }
        }
    }

    function reportStakingModuleExitedKeysCountByNodeOperator(
        uint256 _stakingModuleId,
        uint256[] calldata _nodeOperatorIds,
        uint256[] calldata _exitedKeysCounts
    )
        external
        onlyRole(REPORT_EXITED_KEYS_ROLE)
    {
        StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleId);
        address moduleAddr = stakingModule.stakingModuleAddress;
        (uint256 prevExitedKeysCount,,) = IStakingModule(moduleAddr).getValidatorsKeysStats();
        uint256 newExitedKeysCount;
        for (uint256 i = 0; i < _nodeOperatorIds.length; ) {
            newExitedKeysCount = IStakingModule(moduleAddr)
                .updateExitedValidatorsKeysCount(_nodeOperatorIds[i], _exitedKeysCounts[i]);
            unchecked { ++i; }
        }
        uint256 prevReportedExitedKeysCount = stakingModule.exitedKeysCount;
        if (prevExitedKeysCount < prevReportedExitedKeysCount &&
            newExitedKeysCount >= prevReportedExitedKeysCount
        ) {
            // oracle finished updating exited keys for all node ops
            IStakingModule(moduleAddr).finishUpdatingExitedValidatorsKeysCount();
        }
    }

    struct KeysCountCorrection {
        uint256 currentModuleExitedKeysCount;
        uint256 currentNodeOperatorExitedKeysCount;
        uint256 currentNodeOperatorStuckKeysCount;
        uint256 newModuleExitedKeysCount;
        uint256 newNodeOperatorExitedKeysCount;
        uint256 newNodeOperatorStuckKeysCount;
    }

    /**
     * @notice Sets exited keys count for the given module and given node operator in that module
     * without performing critical safety checks, e.g. that exited keys count cannot decrease.
     *
     * Should only be used by the DAO in extreme cases and with sufficient precautions to correct
     * invalid data reported by the oracle committee due to a bug in the oracle daemon.
     *
     * @param _stakingModuleId ID of the staking module.
     *
     * @param _nodeOperatorId ID of the node operator.
     *
     * @param _triggerUpdateFinish Whether to call `finishUpdatingExitedValidatorsKeysCount` on
     *        the module after applying the corrections.
     *
     * @param _correction.currentModuleExitedKeysCount The expected current number of exited keys
     *        of the module that is being corrected.
     *
     * @param _correction.currentNodeOperatorExitedKeysCount The expected current number of exited
     *        keys of the node operator that is being corrected.
     *
     * @param _correction.currentNodeOperatorStuckKeysCount The expected current number of stuck
     *        keys of the node operator that is being corrected.
     *
     * @param _correction.newModuleExitedKeysCount The corrected number of exited keys of the module.
     *
     * @param _correction.newNodeOperatorExitedKeysCount The corrected number of exited keys of the
     *        node operator.
     *
     * @param _correction.newNodeOperatorStuckKeysCount The corrected number of stuck keys of the
     *        node operator.
     *
     * Reverts if the current numbers of exited and stuck keys of the module and node operator don't
     * match the supplied expected current values.
     */
    function unsafeSetExitedKeysCount(
        uint256 _stakingModuleId,
        uint256 _nodeOperatorId,
        bool _triggerUpdateFinish,
        KeysCountCorrection memory _correction
    )
        external
        onlyRole(UNSAFE_SET_EXITED_KEYS_ROLE)
    {
        StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleId);
        address moduleAddr = stakingModule.stakingModuleAddress;

        (uint256 nodeOpExitedKeysCount,,) = IStakingModule(moduleAddr)
            .getValidatorsKeysStats(_nodeOperatorId);

        // FIXME: get current value from the staking module
        uint256 nodeOpStuckKeysCount;

        if (_correction.currentModuleExitedKeysCount != stakingModule.exitedKeysCount ||
            _correction.currentNodeOperatorExitedKeysCount != nodeOpExitedKeysCount ||
            _correction.currentNodeOperatorStuckKeysCount != nodeOpStuckKeysCount
        ) {
            revert UnexpectedCurrentKeysCount(
                stakingModule.exitedKeysCount,
                nodeOpExitedKeysCount,
                nodeOpStuckKeysCount
            );
        }

        stakingModule.exitedKeysCount = _correction.newModuleExitedKeysCount;

        IStakingModule(moduleAddr).unsafeUpdateValidatorsKeysCount(
            _nodeOperatorId,
            _correction.newNodeOperatorExitedKeysCount,
            _correction.newNodeOperatorStuckKeysCount
        );

        if (_triggerUpdateFinish) {
            IStakingModule(moduleAddr).finishUpdatingExitedValidatorsKeysCount();
        }
    }

    function reportStakingModuleStuckKeysCountByNodeOperator(
        uint256 _stakingModuleId,
        uint256[] calldata _nodeOperatorIds,
        uint256[] calldata _stuckKeysCounts
    )
        external
        onlyRole(REPORT_EXITED_KEYS_ROLE)
    {
        address moduleAddr = _getStakingModuleById(_stakingModuleId).stakingModuleAddress;
        for (uint256 i = 0; i < _nodeOperatorIds.length; ) {
            IStakingModule(moduleAddr).updateStuckValidatorsKeysCount(
                _nodeOperatorIds[i],
                _stuckKeysCounts[i]
            );
            unchecked { ++i; }
        }
    }

    function getExitedKeysCountAcrossAllModules() external view returns (uint256) {
        uint256 stakingModulesCount = getStakingModulesCount();
        uint256 exitedKeysCount = 0;
        for (uint256 i; i < stakingModulesCount; ) {
            exitedKeysCount += _getStakingModuleByIndex(i).exitedKeysCount;
            unchecked { ++i; }
        }
        return exitedKeysCount;
    }

    /**
     * @notice Returns all registered staking modules
     */
    function getStakingModules() external view returns (StakingModule[] memory res) {
        uint256 stakingModulesCount = getStakingModulesCount();
        res = new StakingModule[](stakingModulesCount);
        for (uint256 i; i < stakingModulesCount; ) {
            res[i] = _getStakingModuleByIndex(i);
            unchecked {
                ++i;
            }
        }
    }

    /**
     * @notice Returns the ids of all registered staking modules
     */
    function getStakingModuleIds() external view returns (uint24[] memory stakingModuleIds) {
        uint256 stakingModulesCount = getStakingModulesCount();
        stakingModuleIds = new uint24[](stakingModulesCount);
        for (uint256 i; i < stakingModulesCount; ) {
            stakingModuleIds[i] = _getStakingModuleByIndex(i).id;
            unchecked {
                ++i;
            }
        }
    }

    /**
     *  @dev Returns staking module by id
     */
    function getStakingModule(uint256 _stakingModuleId)
        external
        view
        validStakingModuleId(_stakingModuleId)
        returns (StakingModule memory)
    {
        return _getStakingModuleById(_stakingModuleId);
    }

    /**
     * @dev Returns total number of staking modules
     */
    function getStakingModulesCount() public view returns (uint256) {
        return STAKING_MODULES_COUNT_POSITION.getStorageUint256();
    }

    /**
     * @dev Returns status of staking module
     */
    function getStakingModuleStatus(uint256 _stakingModuleId) public view
        validStakingModuleId(_stakingModuleId)
        returns (StakingModuleStatus)
    {
        return StakingModuleStatus(_getStakingModuleById(_stakingModuleId).status);
    }

    /**
     * @notice set the staking module status flag for participation in further deposits and/or reward distribution
     */
    function setStakingModuleStatus(uint256 _stakingModuleId, StakingModuleStatus _status) external
        validStakingModuleId(_stakingModuleId)
        onlyRole(STAKING_MODULE_MANAGE_ROLE)
    {
        StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleId);
        StakingModuleStatus _prevStatus = StakingModuleStatus(stakingModule.status);
        if (_prevStatus == _status) revert ErrorStakingModuleStatusTheSame();
        stakingModule.status = uint8(_status);
        emit StakingModuleStatusSet(uint24(_stakingModuleId), _status, msg.sender);
    }

    /**
     * @notice pause deposits for staking module
     * @param _stakingModuleId id of the staking module to be paused
     */
    function pauseStakingModule(uint256 _stakingModuleId) external
        validStakingModuleId(_stakingModuleId)
        onlyRole(STAKING_MODULE_PAUSE_ROLE)
    {
        StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleId);
        StakingModuleStatus _prevStatus = StakingModuleStatus(stakingModule.status);
        if (_prevStatus != StakingModuleStatus.Active) revert ErrorStakingModuleNotActive();
        stakingModule.status = uint8(StakingModuleStatus.DepositsPaused);
        emit StakingModuleStatusSet(uint24(_stakingModuleId), StakingModuleStatus.DepositsPaused, msg.sender);
    }

    /**
     * @notice resume deposits for staking module
     * @param _stakingModuleId id of the staking module to be unpaused
     */
    function resumeStakingModule(uint256 _stakingModuleId) external
        validStakingModuleId(_stakingModuleId)
        onlyRole(STAKING_MODULE_RESUME_ROLE)
    {
        StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleId);
        StakingModuleStatus _prevStatus = StakingModuleStatus(stakingModule.status);
        if (_prevStatus != StakingModuleStatus.DepositsPaused) revert ErrorStakingModuleNotPaused();
        stakingModule.status = uint8(StakingModuleStatus.Active);
        emit StakingModuleStatusSet(uint24(_stakingModuleId), StakingModuleStatus.Active, msg.sender);
    }

    function getStakingModuleIsStopped(uint256 _stakingModuleId) external view
        validStakingModuleId(_stakingModuleId)
        returns (bool)
    {
        return getStakingModuleStatus(_stakingModuleId) == StakingModuleStatus.Stopped;
    }

    function getStakingModuleIsDepositsPaused(uint256 _stakingModuleId) external view
        validStakingModuleId(_stakingModuleId)
        returns (bool)
    {
        return getStakingModuleStatus(_stakingModuleId) == StakingModuleStatus.DepositsPaused;
    }

    function getStakingModuleIsActive(uint256 _stakingModuleId) external view
        validStakingModuleId(_stakingModuleId)
        returns (bool)
    {
        return getStakingModuleStatus(_stakingModuleId) == StakingModuleStatus.Active;
    }

    function getStakingModuleKeysOpIndex(uint256 _stakingModuleId) external view
        validStakingModuleId(_stakingModuleId)
        returns (uint256)
    {
        return IStakingModule(_getStakingModuleAddressById(_stakingModuleId)).getValidatorsKeysNonce();
    }

    function getStakingModuleLastDepositBlock(uint256 _stakingModuleId) external view
        validStakingModuleId(_stakingModuleId)
        returns (uint256)
    {
        StakingModule storage stakingModule = _getStakingModuleById(_stakingModuleId);
        return stakingModule.lastDepositBlock;
    }

    function getStakingModuleActiveKeysCount(uint256 _stakingModuleId) external view
        validStakingModuleId(_stakingModuleId)
        returns (uint256 activeKeysCount)
    {
        (, activeKeysCount, ) = IStakingModule(_getStakingModuleAddressById(_stakingModuleId)).getValidatorsKeysStats();
    }

    /**
     * @dev calculate max count of depositable staking module keys based on the current Staking Router balance and buffered Ether amount
     *
     * @param _stakingModuleId id of the staking module to be deposited
     * @return max depositable keys count
     */
    function getStakingModuleMaxDepositableKeys(uint256 _stakingModuleId) public view
        validStakingModuleId(_stakingModuleId)
        returns (uint256)
    {
        uint256 stakingModuleIndex = _getStakingModuleIndexById(uint24(_stakingModuleId));
        uint256 _keysToAllocate = getLido().getBufferedEther() / DEPOSIT_SIZE;
        (, uint256[] memory newKeysAllocation, StakingModuleCache[] memory stakingModulesCache) = _getKeysAllocation(_keysToAllocate);
        return newKeysAllocation[stakingModuleIndex] - stakingModulesCache[stakingModuleIndex].activeKeysCount;
    }

    /**
     * @notice Returns the aggregate fee distribution proportion
     * @return modulesFee modules aggregate fee in base precision
     * @return treasuryFee treasury fee in base precision
     * @return basePrecision base precision: a value corresponding to the full fee
     */
    function getStakingFeeAggregateDistribution() public view returns (
        uint96 modulesFee,
        uint96 treasuryFee,
        uint256 basePrecision
    ) {
        uint96[] memory moduleFees;
        uint96 totalFee;
        (, , moduleFees, totalFee, basePrecision) = getStakingRewardsDistribution();
        for (uint256 i; i < moduleFees.length; ++i) {
            modulesFee += moduleFees[i];
        }
        treasuryFee = totalFee - modulesFee;
    }

    /**
     * @notice Return shares table
     *
     * @return recipients rewards recipient addresses corresponding to each module
     * @return stakingModuleIds module IDs
     * @return stakingModuleFees fee of each recipient
     * @return totalFee total fee to mint for each staking module and treasury
     * @return precisionPoints base precision number, which constitutes 100% fee
     */
    function getStakingRewardsDistribution()
        public
        view
        returns (
            address[] memory recipients,
            uint256[] memory stakingModuleIds,
            uint96[] memory stakingModuleFees,
            uint96 totalFee,
            uint256 precisionPoints
        )
    {
        (uint256 totalActiveKeys, StakingModuleCache[] memory stakingModulesCache) = _loadStakingModulesCache(false);
        uint256 stakingModulesCount = stakingModulesCache.length;

        /// @dev return empty response if there are no staking modules or active keys yet
        if (stakingModulesCount == 0 || totalActiveKeys == 0) {
            return (new address[](0), new uint256[](0), new uint96[](0), 0, FEE_PRECISION_POINTS);
        }

        precisionPoints = FEE_PRECISION_POINTS;
        stakingModuleIds = new uint256[](stakingModulesCount);
        recipients = new address[](stakingModulesCount);
        stakingModuleFees = new uint96[](stakingModulesCount);

        uint256 rewardedStakingModulesCount = 0;
        uint256 stakingModuleKeysShare;
        uint96 stakingModuleFee;

        for (uint256 i; i < stakingModulesCount; ) {
            stakingModuleIds[i] = stakingModulesCache[i].stakingModuleId;
            /// @dev skip staking modules which have no active keys
            if (stakingModulesCache[i].activeKeysCount > 0) {
                stakingModuleKeysShare = ((stakingModulesCache[i].activeKeysCount * precisionPoints) / totalActiveKeys);

                recipients[rewardedStakingModulesCount] = address(stakingModulesCache[i].stakingModuleAddress);
                stakingModuleFee = uint96((stakingModuleKeysShare * stakingModulesCache[i].stakingModuleFee) / TOTAL_BASIS_POINTS);
                /// @dev if the staking module has the `Stopped` status for some reason, then
                ///      the staking module's rewards go to the treasury, so that the DAO has ability
                ///      to manage them (e.g. to compensate the staking module in case of an error, etc.)
                if (stakingModulesCache[i].status != StakingModuleStatus.Stopped) {
                    stakingModuleFees[rewardedStakingModulesCount] = stakingModuleFee;
                }
                // else keep stakingModuleFees[rewardedStakingModulesCount] = 0, but increase totalFee

                totalFee += (uint96((stakingModuleKeysShare * stakingModulesCache[i].treasuryFee) / TOTAL_BASIS_POINTS) + stakingModuleFee);

                unchecked {
                    rewardedStakingModulesCount++;
                }
            }
            unchecked {
                ++i;
            }
        }

        // sanity check
        if (totalFee >= precisionPoints) revert ErrorValueOver100Percent("totalFee");

        /// @dev shrink arrays
        if (rewardedStakingModulesCount < stakingModulesCount) {
            uint256 trim = stakingModulesCount - rewardedStakingModulesCount;
            assembly {
                mstore(recipients, sub(mload(recipients), trim))
                mstore(stakingModuleFees, sub(mload(stakingModuleFees), trim))
            }
        }
    }

    /// @notice Helper for Lido contract (DEPRECATED)
    ///         Returns total fee total fee to mint for each staking
    ///         module and treasury in reduced, 1e4 precision.
    ///         In integrations please use getStakingRewardsDistribution().
    ///         reduced, 1e4 precision.
    function getTotalFeeE4Precision() external view returns (uint16 totalFee) {
        /// @dev The logic is placed here but in Lido contract to save Lido bytecode
        uint256 E4_BASIS_POINTS = 10000;  // Corresponds to Lido.TOTAL_BASIS_POINTS
        (, , , uint96 totalFeeInHighPrecision, uint256 precision) = getStakingRewardsDistribution();
        // Here we rely on (totalFeeInHighPrecision <= precision)
        totalFee = uint16((totalFeeInHighPrecision * E4_BASIS_POINTS) / precision);
    }

    /// @notice Helper for Lido contract (DEPRECATED)
    ///         Returns the same as getStakingFeeAggregateDistribution() but in reduced, 1e4 precision
    /// @dev Helper only for Lido contract. Use getStakingFeeAggregateDistribution() instead
    function getStakingFeeAggregateDistributionE4Precision()
        external view
        returns (uint16 modulesFee, uint16 treasuryFee)
    {
        /// @dev The logic is placed here but in Lido contract to save Lido bytecode
        uint256 E4_BASIS_POINTS = 10000;  // Corresponds to Lido.TOTAL_BASIS_POINTS
        (
            uint256 modulesFeeHighPrecision,
            uint256 treasuryFeeHighPrecision,
            uint256 precision
        ) = getStakingFeeAggregateDistribution();
        // Here we rely on ({modules,treasury}FeeHighPrecision <= precision)
        modulesFee = uint16((modulesFeeHighPrecision * E4_BASIS_POINTS) / precision);
        treasuryFee = uint16((treasuryFeeHighPrecision * E4_BASIS_POINTS) / precision);
    }

    /// @notice returns new deposits allocation after the distribution of the `_keysToAllocate` keys
    function getKeysAllocation(uint256 _keysToAllocate) external view returns (uint256 allocated, uint256[] memory allocations) {
        (allocated, allocations, ) = _getKeysAllocation(_keysToAllocate);
    }

    /**
     * @dev Invokes a deposit call to the official Deposit contract
     * @param _maxDepositsCount max deposits count
     * @param _stakingModuleId id of the staking module to be deposited
     * @param _depositCalldata staking module calldata
     */
    function deposit(
        uint256 _maxDepositsCount,
        uint256 _stakingModuleId,
        bytes calldata _depositCalldata
    ) external payable validStakingModuleId(_stakingModuleId)  returns (uint256 keysCount) {
        if (msg.sender != LIDO_POSITION.getStorageAddress()) revert ErrorAppAuthLidoFailed();

        uint256 depositableEth = msg.value;
        if (depositableEth == 0) {
            _transferBalanceEthToLido();
            return 0;
        }

        bytes32 withdrawalCredentials = getWithdrawalCredentials();
        if (withdrawalCredentials == 0) revert ErrorEmptyWithdrawalsCredentials();

        uint256 stakingModuleIndex = _getStakingModuleIndexById(_stakingModuleId);
        StakingModule storage stakingModule = _getStakingModuleByIndex(stakingModuleIndex);
        if (StakingModuleStatus(stakingModule.status) != StakingModuleStatus.Active) revert ErrorStakingModuleNotActive();

        uint256 maxDepositableKeys = getStakingModuleMaxDepositableKeys(_stakingModuleId);
        uint256 keysToDeposit = Math256.min(maxDepositableKeys, _maxDepositsCount);

        if (keysToDeposit > 0) {
            bytes memory publicKeysBatch;
            bytes memory signaturesBatch;
            (keysCount, publicKeysBatch, signaturesBatch) = IStakingModule(stakingModule.stakingModuleAddress)
                .requestValidatorsKeysForDeposits(keysToDeposit, _depositCalldata);

            if (keysCount > 0) {
                _makeBeaconChainDeposits32ETH(keysCount, abi.encodePacked(withdrawalCredentials), publicKeysBatch, signaturesBatch);

                stakingModule.lastDepositAt = uint64(block.timestamp);
                stakingModule.lastDepositBlock = block.number;

                emit StakingRouterETHDeposited(uint24(_stakingModuleId), keysCount * DEPOSIT_SIZE);
            }
        }
        _transferBalanceEthToLido();
    }

    /// @dev transfer all remaining balance to Lido contract
    function _transferBalanceEthToLido() internal {
        uint256 balance = address(this).balance;
        if (balance > 0) {
            getLido().receiveStakingRouterDepositRemainder{value: balance}();
        }
    }

    /**
     * @notice Set credentials to withdraw ETH on Consensus Layer side after the phase 2 is launched to `_withdrawalCredentials`
     * @dev Note that setWithdrawalCredentials discards all unused signing keys as the signatures are invalidated.
     * @param _withdrawalCredentials withdrawal credentials field as defined in the Ethereum PoS consensus specs
     */
    function setWithdrawalCredentials(bytes32 _withdrawalCredentials) external onlyRole(MANAGE_WITHDRAWAL_CREDENTIALS_ROLE) {
        WITHDRAWAL_CREDENTIALS_POSITION.setStorageBytes32(_withdrawalCredentials);

        //trim keys with old WC
        _trimUnusedKeys();

        emit WithdrawalCredentialsSet(_withdrawalCredentials, msg.sender);
    }

    /**
     * @notice Returns current credentials to withdraw ETH on Consensus Layer side after the phase 2 is launched
     */
    function getWithdrawalCredentials() public view returns (bytes32) {
        return WITHDRAWAL_CREDENTIALS_POSITION.getStorageBytes32();
    }

    function _trimUnusedKeys() internal {
        uint256 stakingModulesCount = getStakingModulesCount();
        for (uint256 i; i < stakingModulesCount; ) {
            IStakingModule(_getStakingModuleAddressByIndex(i)).invalidateReadyToDepositKeys();
            unchecked {
                ++i;
            }
        }
    }

    /**
     * @dev load modules into a memory cache
     *
     * @param _zeroKeysCountsOfInactiveModules if true, active and available keys for
     *        inactive modules are set to zero
     *
     * @return totalActiveKeys total active keys across all modules (excluding inactive
     *         if _zeroKeysCountsOfInactiveModules is true)
     * @return stakingModulesCache array of StakingModuleCache structs
     */
    function _loadStakingModulesCache(bool _zeroKeysCountsOfInactiveModules) internal view returns (
        uint256 totalActiveKeys,
        StakingModuleCache[] memory stakingModulesCache
    ) {
        uint256 stakingModulesCount = getStakingModulesCount();
        stakingModulesCache = new StakingModuleCache[](stakingModulesCount);
        for (uint256 i; i < stakingModulesCount; ) {
            stakingModulesCache[i] = _loadStakingModulesCacheItem(i, _zeroKeysCountsOfInactiveModules);
            totalActiveKeys += stakingModulesCache[i].activeKeysCount;
            unchecked {
                ++i;
            }
        }
    }

    function _loadStakingModulesCacheItem(
        uint256 _stakingModuleIndex,
        bool _zeroKeysCountsIfInactive
    ) internal view returns (StakingModuleCache memory cacheItem) {
        StakingModule storage stakingModuleData = _getStakingModuleByIndex(_stakingModuleIndex);

        cacheItem.stakingModuleAddress = stakingModuleData.stakingModuleAddress;
        cacheItem.stakingModuleId = stakingModuleData.id;
        cacheItem.stakingModuleFee = stakingModuleData.stakingModuleFee;
        cacheItem.treasuryFee = stakingModuleData.treasuryFee;
        cacheItem.targetShare = stakingModuleData.targetShare;
        cacheItem.status = StakingModuleStatus(stakingModuleData.status);

        if (!_zeroKeysCountsIfInactive || cacheItem.status == StakingModuleStatus.Active) {
            uint256 moduleExitedKeysCount;
            (moduleExitedKeysCount, cacheItem.activeKeysCount, cacheItem.availableKeysCount) =
                IStakingModule(cacheItem.stakingModuleAddress).getValidatorsKeysStats();
            uint256 exitedKeysCount = stakingModuleData.exitedKeysCount;
            if (exitedKeysCount > moduleExitedKeysCount) {
                // module hasn't received all exited validators data yet => we need to correct
                // activeKeysCount (equal to depositedKeysCount - exitedKeysCount) replacing
                // the exitedKeysCount with the one that staking router is aware of
                cacheItem.activeKeysCount -= (exitedKeysCount - moduleExitedKeysCount);
            }
        }
    }

    function _getKeysAllocation(
        uint256 _keysToAllocate
    ) internal view returns (uint256 allocated, uint256[] memory allocations, StakingModuleCache[] memory stakingModulesCache) {
        // calculate total used keys for operators
        uint256 totalActiveKeys;

        (totalActiveKeys, stakingModulesCache) = _loadStakingModulesCache(true);

        uint256 stakingModulesCount = stakingModulesCache.length;
        allocations = new uint256[](stakingModulesCount);
        if (stakingModulesCount > 0) {
            /// @dev new estimated active keys count
            totalActiveKeys += _keysToAllocate;
            uint256[] memory capacities = new uint256[](stakingModulesCount);
            uint256 targetKeys;

            for (uint256 i; i < stakingModulesCount; ) {
                allocations[i] = stakingModulesCache[i].activeKeysCount;
                targetKeys = (stakingModulesCache[i].targetShare * totalActiveKeys) / TOTAL_BASIS_POINTS;
                capacities[i] = Math256.min(targetKeys, stakingModulesCache[i].activeKeysCount + stakingModulesCache[i].availableKeysCount);
                unchecked {
                    ++i;
                }
            }

            allocated = MinFirstAllocationStrategy.allocate(allocations, capacities, _keysToAllocate);
        }
    }

    function _getStakingModuleIndexById(uint256 _stakingModuleId) internal view returns (uint256) {
        mapping(uint256 => uint256) storage _stakingModuleIndicesOneBased = _getStorageStakingIndicesMapping();
        uint256 indexOneBased = _stakingModuleIndicesOneBased[_stakingModuleId];
        if (indexOneBased == 0) revert ErrorStakingModuleUnregistered();
        return indexOneBased - 1;
    }

    function _setStakingModuleIndexById(uint256 _stakingModuleId, uint256 _stakingModuleIndex) internal {
        mapping(uint256 => uint256) storage _stakingModuleIndicesOneBased = _getStorageStakingIndicesMapping();
        _stakingModuleIndicesOneBased[_stakingModuleId] = _stakingModuleIndex + 1;
    }

    function _getStakingModuleById(uint256 _stakingModuleId) internal view returns (StakingModule storage) {
        return _getStakingModuleByIndex(_getStakingModuleIndexById(_stakingModuleId));
    }

    function _getStakingModuleByIndex(uint256 _stakingModuleIndex) internal view returns (StakingModule storage) {
        mapping(uint256 => StakingModule) storage _stakingModules = _getStorageStakingModulesMapping();
        return _stakingModules[_stakingModuleIndex];
    }

    function _getStakingModuleAddressById(uint256 _stakingModuleId) internal view returns (address) {
        return _getStakingModuleById(_stakingModuleId).stakingModuleAddress;
    }

    function _getStakingModuleAddressByIndex(uint256 _stakingModuleIndex) internal view returns (address) {
        return _getStakingModuleByIndex(_stakingModuleIndex).stakingModuleAddress;
    }


    function _getStorageStakingModulesMapping() internal pure returns (mapping(uint256 => StakingModule) storage result) {
        bytes32 position = STAKING_MODULES_MAPPING_POSITION;
        assembly {
            result.slot := position
        }
    }

    function _getStorageStakingIndicesMapping() internal pure returns (mapping(uint256 => uint256) storage result) {
        bytes32 position = STAKING_MODULE_INDICES_MAPPING_POSITION;
        assembly {
            result.slot := position
        }
    }
}
