const { assert } = require('chai')
const { BN } = require('bn.js')
const { assertBn } = require('@aragon/contract-helpers-test/src/asserts')
const { getEventArgument } = require('@aragon/contract-helpers-test')

const { pad, toBN, ETH, tokens, hexConcat } = require('../helpers/utils')

const { DSMAttestMessage, DSMPauseMessage } = require('../helpers/signatures')
const { waitBlocks } = require('../helpers/blockchain')
const { deployProtocol } = require('../helpers/protocol')
const { setupNodeOperatorsRegistry } = require('../helpers/staking-modules')
const { gwei, ZERO_HASH } = require('../helpers/utils')
const { pushOracleReport } = require('../helpers/oracle')

const NodeOperatorsRegistry = artifacts.require('NodeOperatorsRegistry')
const CURATED_MODULE_ID = 1

const makeAccountingReport = ({refSlot, numValidators, clBalanceGwei}) => ({
  refSlot,
  consensusVersion: 1,
  numValidators: numValidators,
  clBalanceGwei: clBalanceGwei,
  stakingModuleIdsWithNewlyExitedValidators: [],
  numExitedValidatorsByStakingModule: [],
  withdrawalVaultBalance: 0,
  elRewardsVaultBalance: 0,
  lastWithdrawalRequestIdToFinalize: 0,
  finalizationShareRate: 0,
  isBunkerMode: false,
  extraDataFormat: 0,
  extraDataHash: ZERO_HASH,
  extraDataItemsCount: 0,
})

contract('Lido: happy path', (addresses) => {
  const [
    // node operators
    operator_1,
    operator_2,
    operator_3,
    // users who deposit Ether to the pool
    user1,
    user2,
    user3,
    // unrelated address
    nobody
  ] = addresses

  let pool, nodeOperatorsRegistry, token
  let oracle, depositContractMock
  let treasuryAddr, guardians, voting
  let depositSecurityModule, depositRoot
  let withdrawalCredentials, stakingRouter
  let consensus

  before('DAO, node operators registry, token, pool and deposit security module are deployed and initialized', async () => {
      const deployed = await deployProtocol({
        stakingModulesFactory: async (protocol) => {
          const curatedModule = await setupNodeOperatorsRegistry(protocol)
          return [
            {
              module: curatedModule,
              name: 'Curated',
              targetShares: 10000,
              moduleFee: 500,
              treasuryFee: 500
            }
          ]
        }
      })

      // contracts/StETH.sol
      token = deployed.pool

      // contracts/Lido.sol
      pool = deployed.pool

      // contracts/nos/NodeOperatorsRegistry.sol
      nodeOperatorsRegistry = deployed.stakingModules[0]

      // contracts/0.8.9/StakingRouter.sol
      stakingRouter = deployed.stakingRouter

      // mocks
      oracle = deployed.oracle
      depositContractMock = deployed.depositContract
      consensus = deployed.consensusContract

      // addresses
      treasuryAddr = deployed.treasury.address
      depositSecurityModule = deployed.depositSecurityModule
      guardians = deployed.guardians
      voting = deployed.voting.address

      depositRoot = await depositContractMock.get_deposit_root()
      withdrawalCredentials = '0x'.padEnd(66, '1234')

      await stakingRouter.setWithdrawalCredentials(withdrawalCredentials, { from: voting })
    }
  )

  // Fee and its distribution are in basis points, 10000 corresponding to 100%

  // Total fee is 10%
  const totalFeePoints = 0.1 * 10000

  it('voting sets fee and its distribution', async () => {
    // Fee and distribution were set
    // assertBn(await pool.getFee({ from: nobody }), totalFeePoints, 'total fee')
    // const distribution = await pool.getFeeDistribution({ from: nobody })
    // console.log('distribution', distribution)
    // assertBn(distribution.treasuryFeeBasisPoints, treasuryFeePoints, 'treasury fee')
    // assertBn(distribution.operatorsFeeBasisPoints, nodeOperatorsFeePoints, 'node operators fee')
  })

  it('voting sets withdrawal credentials', async () => {
    const wc = '0x'.padEnd(66, '1234')
    assert.equal(await pool.getWithdrawalCredentials({ from: nobody }), wc, 'withdrawal credentials')

    withdrawalCredentials = '0x'.padEnd(66, '5678')
    await stakingRouter.setWithdrawalCredentials(withdrawalCredentials, { from: voting })

    // Withdrawal credentials were set

    assert.equal(await stakingRouter.getWithdrawalCredentials({ from: nobody }), withdrawalCredentials, 'withdrawal credentials')
  })

  // Each node operator has its Ethereum 1 address, a name and a set of registered
  // validators, each of them defined as a (public key, signature) pair
  const nodeOperator1 = {
    name: 'operator_1',
    address: operator_1,
    validators: [
      {
        key: pad('0x010101', 48),
        sig: pad('0x01', 96)
      }
    ]
  }

  it('voting adds the first node operator', async () => {
    const txn = await nodeOperatorsRegistry.addNodeOperator(nodeOperator1.name, nodeOperator1.address, { from: voting })

    // Some Truffle versions fail to decode logs here, so we're decoding them explicitly using a helper
    nodeOperator1.id = getEventArgument(txn, 'NodeOperatorAdded', 'nodeOperatorId', { decodeForAbi: NodeOperatorsRegistry._json.abi })
    assertBn(nodeOperator1.id, 0, 'operator id')

    assertBn(await nodeOperatorsRegistry.getNodeOperatorsCount(), 1, 'total node operators')
  })

  it('the first node operator registers one validator', async () => {
    // How many validators can this node operator register
    const validatorsLimit = 1000000000
    const numKeys = 1

    await nodeOperatorsRegistry.addSigningKeysOperatorBH(
      nodeOperator1.id,
      numKeys,
      nodeOperator1.validators[0].key,
      nodeOperator1.validators[0].sig,
      {
        from: nodeOperator1.address
      }
    )

    await nodeOperatorsRegistry.setNodeOperatorStakingLimit(0, validatorsLimit, { from: voting })

    // The key was added

    const totalKeys = await nodeOperatorsRegistry.getTotalSigningKeyCount(nodeOperator1.id, { from: nobody })
    assertBn(totalKeys, 1, 'total signing keys')

    // The key was not used yet

    const unusedKeys = await nodeOperatorsRegistry.getUnusedSigningKeyCount(nodeOperator1.id, { from: nobody })
    assertBn(unusedKeys, 1, 'unused signing keys')
  })

  it('the first user deposits 3 ETH to the pool', async () => {
    await web3.eth.sendTransaction({ to: pool.address, from: user1, value: ETH(3) })
    const block = await web3.eth.getBlock('latest')
    const keysOpIndex = await nodeOperatorsRegistry.getKeysOpIndex()

    DSMAttestMessage.setMessagePrefix(await depositSecurityModule.ATTEST_MESSAGE_PREFIX())
    DSMPauseMessage.setMessagePrefix(await depositSecurityModule.PAUSE_MESSAGE_PREFIX())

    const validAttestMessage = new DSMAttestMessage(block.number, block.hash, depositRoot, CURATED_MODULE_ID, keysOpIndex)
    const signatures = [
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[0]]),
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[1]])
    ]
    await depositSecurityModule.depositBufferedEther(
      block.number,
      block.hash,
      depositRoot,
      CURATED_MODULE_ID,
      keysOpIndex,
      '0x',
      signatures
    )

    // No Ether was deposited yet to the validator contract

    assertBn(await depositContractMock.totalCalls(), 0)

    const ether2Stat = await pool.getBeaconStat()
    assertBn(ether2Stat.depositedValidators, 0, 'deposited ether2')
    assertBn(ether2Stat.beaconBalance, 0, 'remote ether2')

    // All Ether was buffered within the pool contract atm

    assertBn(await pool.getBufferedEther(), ETH(3), 'buffered ether')
    assertBn(await pool.getTotalPooledEther(), ETH(3), 'total pooled ether')

    // The amount of tokens corresponding to the deposited ETH value was minted to the user

    assertBn(await token.balanceOf(user1), tokens(3), 'user1 tokens')

    assertBn(await token.totalSupply(), tokens(3), 'token total supply')
  })

  it('the second user deposits 30 ETH to the pool', async () => {
    await web3.eth.sendTransaction({ to: pool.address, from: user2, value: ETH(30) })
    const block = await waitBlocks(await depositSecurityModule.getMinDepositBlockDistance())
    const keysOpIndex = await nodeOperatorsRegistry.getKeysOpIndex()

    DSMAttestMessage.setMessagePrefix(await depositSecurityModule.ATTEST_MESSAGE_PREFIX())
    DSMPauseMessage.setMessagePrefix(await depositSecurityModule.PAUSE_MESSAGE_PREFIX())

    const validAttestMessage = new DSMAttestMessage(block.number, block.hash, depositRoot, CURATED_MODULE_ID, keysOpIndex)
    const signatures = [
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[0]]),
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[1]])
    ]
    await depositSecurityModule.depositBufferedEther(
      block.number,
      block.hash,
      depositRoot,
      CURATED_MODULE_ID,
      keysOpIndex,
      '0x',
      signatures
    )

    // The first 32 ETH chunk was deposited to the deposit contract,
    // using public key and signature of the only validator of the first operator

    assertBn(await depositContractMock.totalCalls(), 1)

    const regCall = await depositContractMock.calls.call(0)
    assert.equal(regCall.pubkey, nodeOperator1.validators[0].key)
    assert.equal(regCall.withdrawal_credentials, withdrawalCredentials)
    assert.equal(regCall.signature, nodeOperator1.validators[0].sig)
    assertBn(regCall.value, ETH(32))

    const ether2Stat = await pool.getBeaconStat()
    assertBn(ether2Stat.depositedValidators, 1, 'deposited ether2')
    assertBn(ether2Stat.beaconBalance, 0, 'remote ether2')

    // Some Ether remained buffered within the pool contract

    assertBn(await pool.getBufferedEther(), ETH(1), 'buffered ether')
    assertBn(await pool.getTotalPooledEther(), ETH(1 + 32), 'total pooled ether')

    // The amount of tokens corresponding to the deposited ETH value was minted to the users

    assertBn(await token.balanceOf(user1), tokens(3), 'user1 tokens')
    assertBn(await token.balanceOf(user2), tokens(30), 'user2 tokens')

    assertBn(await token.totalSupply(), tokens(3 + 30), 'token total supply')
  })

  it('at this point, the pool has ran out of signing keys', async () => {
    const unusedKeys = await nodeOperatorsRegistry.getUnusedSigningKeyCount(nodeOperator1.id, { from: nobody })
    assertBn(unusedKeys, 0, 'unused signing keys')
  })

  const nodeOperator2 = {
    name: 'operator_2',
    address: operator_2,
    validators: [
      {
        key: pad('0x020202', 48),
        sig: pad('0x02', 96)
      }
    ]
  }

  it('voting adds the second node operator who registers one validator', async () => {
    // TODO: we have to submit operators with 0 validators allowed only
    const validatorsLimit = 1000000000

    const txn = await nodeOperatorsRegistry.addNodeOperator(nodeOperator2.name, nodeOperator2.address, { from: voting })

    // Some Truffle versions fail to decode logs here, so we're decoding them explicitly using a helper
    nodeOperator2.id = getEventArgument(txn, 'NodeOperatorAdded', 'nodeOperatorId', { decodeForAbi: NodeOperatorsRegistry._json.abi })
    assertBn(nodeOperator2.id, 1, 'operator id')

    assertBn(await nodeOperatorsRegistry.getNodeOperatorsCount(), 2, 'total node operators')

    const numKeys = 1

    await nodeOperatorsRegistry.addSigningKeysOperatorBH(
      nodeOperator2.id,
      numKeys,
      nodeOperator2.validators[0].key,
      nodeOperator2.validators[0].sig,
      {
        from: nodeOperator2.address
      }
    )

    // The key was added

    await nodeOperatorsRegistry.setNodeOperatorStakingLimit(1, validatorsLimit, { from: voting })

    const totalKeys = await nodeOperatorsRegistry.getTotalSigningKeyCount(nodeOperator2.id, { from: nobody })
    assertBn(totalKeys, 1, 'total signing keys')

    // The key was not used yet

    const unusedKeys = await nodeOperatorsRegistry.getUnusedSigningKeyCount(nodeOperator2.id, { from: nobody })
    assertBn(unusedKeys, 1, 'unused signing keys')
  })

  it('the third user deposits 64 ETH to the pool', async () => {
    await web3.eth.sendTransaction({ to: pool.address, from: user3, value: ETH(64) })

    const block = await waitBlocks(await depositSecurityModule.getMinDepositBlockDistance())
    const keysOpIndex = await nodeOperatorsRegistry.getKeysOpIndex()

    DSMAttestMessage.setMessagePrefix(await depositSecurityModule.ATTEST_MESSAGE_PREFIX())
    DSMPauseMessage.setMessagePrefix(await depositSecurityModule.PAUSE_MESSAGE_PREFIX())

    const validAttestMessage = new DSMAttestMessage(block.number, block.hash, depositRoot, CURATED_MODULE_ID, keysOpIndex)
    const signatures = [
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[0]]),
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[1]])
    ]
    await depositSecurityModule.depositBufferedEther(
      block.number,
      block.hash,
      depositRoot,
      CURATED_MODULE_ID,
      keysOpIndex,
      '0x',
      signatures
    )

    // The first 32 ETH chunk was deposited to the deposit contract,
    // using public key and signature of the only validator of the second operator

    assertBn(await depositContractMock.totalCalls(), 2)

    const regCall = await depositContractMock.calls.call(1)
    assert.equal(regCall.pubkey, nodeOperator2.validators[0].key)
    assert.equal(regCall.withdrawal_credentials, withdrawalCredentials)
    assert.equal(regCall.signature, nodeOperator2.validators[0].sig)
    assertBn(regCall.value, ETH(32))

    const ether2Stat = await pool.getBeaconStat()
    assertBn(ether2Stat.depositedValidators, 2, 'deposited ether2')
    assertBn(ether2Stat.beaconBalance, 0, 'remote ether2')

    // The pool ran out of validator keys, so the remaining 32 ETH were added to the
    // pool buffer

    assertBn(await pool.getBufferedEther(), ETH(1 + 32), 'buffered ether')
    assertBn(await pool.getTotalPooledEther(), ETH(33 + 64), 'total pooled ether')

    // The amount of tokens corresponding to the deposited ETH value was minted to the users

    assertBn(await token.balanceOf(user1), tokens(3), 'user1 tokens')
    assertBn(await token.balanceOf(user2), tokens(30), 'user2 tokens')
    assertBn(await token.balanceOf(user3), tokens(64), 'user3 tokens')

    assertBn(await token.totalSupply(), tokens(3 + 30 + 64), 'token total supply')
  })

  it('the oracle reports balance increase on Ethereum2 side', async () => {

    // Total shares are equal to deposited eth before ratio change and fee mint

    const oldTotalShares = await token.getTotalShares()
    assertBn(oldTotalShares, ETH(97), 'total shares')

    // Old total pooled Ether

    const oldTotalPooledEther = await pool.getTotalPooledEther()
    assertBn(oldTotalPooledEther, ETH(33 + 64), 'total pooled ether')

    // Reporting 1.5-fold balance increase (64 => 96)

    pushOracleReport(consensus, oracle, 2, ETH(96))

    // Total shares increased because fee minted (fee shares added)
    // shares ~= oldTotalShares + reward * oldTotalShares / (newTotalPooledEther - reward)

    const newTotalShares = await token.getTotalShares()
    assertBn(newTotalShares, new BN('99467408585055643879'), 'total shares')

    // Total pooled Ether increased

    const newTotalPooledEther = await pool.getTotalPooledEther()
    assertBn(newTotalPooledEther, ETH(33 + 96), 'total pooled ether')

    // Ether2 stat reported by the pool changed correspondingly

    const ether2Stat = await pool.getBeaconStat()
    assertBn(ether2Stat.depositedValidators, 2, 'deposited ether2')
    assertBn(ether2Stat.beaconBalance, ETH(96), 'remote ether2')

    // Buffered Ether amount didn't change

    assertBn(await pool.getBufferedEther(), ETH(33), 'buffered ether')

    // New tokens was minted to distribute fee
    assertBn(await token.totalSupply(), tokens(129), 'token total supply')

    const reward = toBN(ETH(96 - 64))
    const mintedAmount = new BN(totalFeePoints).mul(reward).divn(10000)

    // Token user balances increased
    assertBn(await token.balanceOf(user1), new BN('3890721649484536082'), 'user1 tokens')
    assertBn(await token.balanceOf(user2), new BN('38907216494845360824'), 'user2 tokens')
    assertBn(await token.balanceOf(user3), new BN('83002061855670103092'), 'user3 tokens')

    // Fee, in the form of minted tokens, was distributed between treasury, insurance fund
    // and node operators
    // treasuryTokenBalance ~= mintedAmount * treasuryFeePoints / 10000
    // insuranceTokenBalance ~= mintedAmount * insuranceFeePoints / 10000
    assertBn(await token.balanceOf(treasuryAddr), new BN('1600000000000000000'), 'treasury tokens')
    assertBn(await token.balanceOf(nodeOperatorsRegistry.address), new BN('1599999999999999999'), 'insurance tokens')

    // The node operators' fee is distributed between all active node operators,
    // proprotional to their effective stake (the amount of Ether staked by the operator's
    // used and non-stopped validators).
    //
    // In our case, both node operators received the same fee since they have the same
    // effective stake (one signing key used from each operator, staking 32 ETH)

    assertBn(await token.balanceOf(nodeOperator1.address), 0, 'operator_1 tokens')
    assertBn(await token.balanceOf(nodeOperator2.address), 0, 'operator_2 tokens')

    // Real minted amount should be a bit less than calculated caused by round errors on mint and transfer operations
    assert(
      mintedAmount
        .sub(new BN(0).add(await token.balanceOf(treasuryAddr)).add(await token.balanceOf(nodeOperatorsRegistry.address)))
        .lt(mintedAmount.divn(100))
    )
  })

  // node operator with 10 validators
  const nodeOperator3 = {
    id: 2,
    name: 'operator_3',
    address: operator_3,
    validators: [...Array(10).keys()].map((i) => ({
      key: pad('0xaa01' + i.toString(16), 48),
      sig: pad('0x' + i.toString(16), 96)
    }))
  }

  it('nodeOperator3 registered in NodeOperatorsRegistry and adds 10 signing keys', async () => {
    const validatorsCount = 10
    await nodeOperatorsRegistry.addNodeOperator(nodeOperator3.name, nodeOperator3.address, { from: voting })
    await nodeOperatorsRegistry.addSigningKeysOperatorBH(
      nodeOperator3.id,
      validatorsCount,
      hexConcat(...nodeOperator3.validators.map((v) => v.key)),
      hexConcat(...nodeOperator3.validators.map((v) => v.sig)),
      {
        from: nodeOperator3.address
      }
    )
    await nodeOperatorsRegistry.setNodeOperatorStakingLimit(nodeOperator3.id, validatorsCount, { from: voting })
  })

  it('nodeOperator3 removes signing key with id 5', async () => {
    const signingKeyIndexToRemove = 5
    await nodeOperatorsRegistry.removeSigningKeyOperatorBH(nodeOperator3.id, signingKeyIndexToRemove, { from: nodeOperator3.address })
    const nodeOperatorInfo = await nodeOperatorsRegistry.getNodeOperator(nodeOperator3.id, false)
    assertBn(nodeOperatorInfo.stakingLimit, 5)
  })

  it('deposit to nodeOperator3 validators', async () => {
    const amountToDeposit = ETH(32 * 10)
    await web3.eth.sendTransaction({ to: pool.address, from: user1, value: amountToDeposit })
    await waitBlocks(await depositSecurityModule.getMinDepositBlockDistance())
    const block = await web3.eth.getBlock('latest')
    const keysOpIndex = await nodeOperatorsRegistry.getKeysOpIndex()

    DSMAttestMessage.setMessagePrefix(await depositSecurityModule.ATTEST_MESSAGE_PREFIX())
    DSMPauseMessage.setMessagePrefix(await depositSecurityModule.PAUSE_MESSAGE_PREFIX())

    const validAttestMessage = new DSMAttestMessage(block.number, block.hash, depositRoot, CURATED_MODULE_ID, keysOpIndex)
    const signatures = [
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[0]]),
      validAttestMessage.sign(guardians.privateKeys[guardians.addresses[1]])
    ]
    await depositSecurityModule.depositBufferedEther(
      block.number,
      block.hash,
      depositRoot,
      CURATED_MODULE_ID,
      keysOpIndex,
      '0x',
      signatures
    )

    let nodeOperatorInfo = await nodeOperatorsRegistry.getNodeOperator(nodeOperator3.id, false)

    // validate that only 5 signing keys used after key removing
    assertBn(nodeOperatorInfo.stakingLimit, nodeOperatorInfo.usedSigningKeys)
    assertBn(nodeOperatorInfo.totalSigningKeys, 9)

    // validate that all other validators used and pool still has buffered ether
    nodeOperatorInfo = await nodeOperatorsRegistry.getNodeOperator(nodeOperator1.id, false)
    assertBn(nodeOperatorInfo.totalSigningKeys, nodeOperatorInfo.usedSigningKeys)
    nodeOperatorInfo = await nodeOperatorsRegistry.getNodeOperator(nodeOperator2.id, false)
    assertBn(nodeOperatorInfo.totalSigningKeys, nodeOperatorInfo.usedSigningKeys)
  })
})
