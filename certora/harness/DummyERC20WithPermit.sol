// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.9;

import {ECDSA} from "@openzeppelin/contracts-v4.4/utils/cryptography/ECDSA.sol";

contract DummyERC20WithPermit {
    uint256 t;
    mapping (address => uint256) b;
    mapping (address => mapping (address => uint256)) a;

    function add(uint a, uint b) internal pure returns (uint256) {
        uint c = a +b;
        require (c >= a);
        return c;
    }
    function sub(uint a, uint b) internal pure returns (uint256) {
        require (a>=b);
        return a-b;
    }

    function totalSupply() external view returns (uint256) {
        return t;
    }
    function balanceOf(address account) external view returns (uint256) {
        return b[account];
    }
    function transfer(address recipient, uint256 amount) external returns (bool) {
        b[msg.sender] = sub(b[msg.sender], amount);
        b[recipient] = add(b[recipient], amount);
        return true;
    }
    function allowance(address owner, address spender) external view returns (uint256) {
        return a[owner][spender];
    }
    function approve(address spender, uint256 amount) external returns (bool) {
        a[msg.sender][spender] = amount;
        return true;
    }

    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external returns (bool) {
        b[sender] = sub(b[sender], amount);
        b[recipient] = add(b[recipient], amount);
        a[sender][msg.sender] = sub(a[sender][msg.sender], amount);
        return true;
    }

    // function unwrapMock(uint256 _wstETHAmount) public returns (uint256) {
    //     return unwrap(_wstETHAmount);
    // }

    function unwrap(uint256 _wstETHAmount) public returns (uint256) {
        return _wstETHAmount;
    }

    // adapted from source: https://github.com/OpenZeppelin/openzeppelin-contracts/blob/6bc1173c8e37ca7de2201a0230bb08e395074da1/contracts/token/ERC20/extensions/ERC20Permit.sol
    //mapping(address account => uint256) private _nonces;
    mapping(address => uint256) private _nonces;

    /**
     * @dev Returns the next unused nonce for an address.
     */
    function nonces(address owner) public view virtual returns (uint256) {
        return _nonces[owner];
    }

    /**
     * @dev Consumes a nonce.
     *
     * Returns the current value and increments nonce.
     */
    function _useNonce(address owner) internal virtual returns (uint256) {
        // For each account, the nonce has an initial value of 0, can only be incremented by one, and cannot be
        // decremented or reset. This guarantees that the nonce never overflows.
        unchecked {
            // It is important to do x++ and not ++x here.
            return _nonces[owner]++;
        }
    }

    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public virtual {
        if (block.timestamp > deadline) {
            //revert ERC2612ExpiredSignature(deadline);
            revert("ERC2612ExpiredSignature");
        }

        bytes32 PERMIT_TYPEHASH =
            keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");

        bytes32 _structHash = keccak256(abi.encode(PERMIT_TYPEHASH, owner, spender, value, _useNonce(owner), deadline));

        // bytes32 hash = _hashTypedDataV4(structHash);
        bytes32 hash = ECDSA.toTypedDataHash(PERMIT_TYPEHASH, _structHash);

        address signer = ECDSA.recover(hash, v, r, s);

        if (signer != owner) {
            //revert ERC2612InvalidSigner(signer, owner);
            revert("ERC2612InvalidSigner");
        }

        //_approve(owner, spender, value);
        if (owner == address(0)) {
            //revert ERC20InvalidApprover(address(0));
            revert("ERC20InvalidApprover");
        }
        if (spender == address(0)) {
            //revert ERC20InvalidSpender(address(0));
            revert("ERC20InvalidSpender");
        }
        //_allowances[owner][spender] = value;
        a[owner][spender] = value;
    }
}