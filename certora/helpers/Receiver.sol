pragma solidity ^0.8.0;

contract Receiver {
    fallback() external payable { }

    bytes returndata;
    function sendTo() external payable {}

    receive() external payable { }
}