methods {
    function getLength() external returns(uint256) envfree;
    function sumOfBuckets() external returns (uint256) envfree;
    function sumOfCapacities() external returns (uint256) envfree;
    function sumOfIncrements() external returns (uint256) envfree;
    function getBucket(uint256) external returns (uint256) envfree;
    function getCapacity(uint256) external returns (uint256) envfree;
    function getIncrement(uint256) external returns (uint256) envfree;

    function addBucket(uint256, uint256) external envfree;
    function allocate(uint256) external returns(uint256) envfree;
}

definition bucketLength() returns uint256 = 5;

function nonOverFlow(uint256 allocationSize) returns bool {
    return sumOfBuckets() + allocationSize <= to_mathint(max_uint);
}

rule allocateDoesntRevert(uint256 allocationSize) {
    require bucketLength() >= getLength();
    require nonOverFlow(allocationSize);
    allocate@withrevert(allocationSize);
    assert !lastReverted;
}

rule sumOfIncrementsEqualsAllocated(uint256 allocationSize) {
    require bucketLength() >= getLength();
    require nonOverFlow(allocationSize);

    uint256 allocated = allocate(allocationSize);

    assert allocated == sumOfIncrements();
    assert allocated <= allocationSize;
}

rule capacityIsNeverSurpassed(uint256 index, uint256 allocationSize) {
    require forall uint256 ind. 
        (ind < bucketLength() => getBucket(ind) <= getCapacity(ind));
    require bucketLength() >= getLength();
    require nonOverFlow(allocationSize);

    uint256 allocated = allocate(allocationSize);

    assert getBucket(index) + getIncrement(index) <= to_mathint(getCapacity(index));
}

rule minimumBucketIsAlwaysIncrementedWhenPossible(uint256 allocationSize) {
    require bucketLength() >= getLength();
    require nonOverFlow(allocationSize);
    uint256 i_min;
    uint256 bucket_min = getBucket(i_min);
    uint256 capacity_min = getCapacity(i_min);

    require forall uint256 indx. 
        (indx < bucketLength() && indx != i_min) =>
        (getBucket(indx) > bucket_min);

    allocate(allocationSize);
    uint256 incr_min = getIncrement(i_min);

    assert incr_min > 0 <=> (allocationSize > 0 && bucket_min < capacity_min);
}
