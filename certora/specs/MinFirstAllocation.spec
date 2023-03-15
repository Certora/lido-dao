methods {
    getLength() returns(uint256) envfree
    sumOfBuckets() returns (uint256) envfree
    sumOfCapacities() returns (uint256) envfree
    sumOfIncrements() returns (uint256) envfree
    getBucket(uint256) returns (uint256) envfree
    getCapacity(uint256) returns (uint256) envfree
    getIncrement(uint256) returns (uint256) envfree

    addBucket(uint256, uint256) envfree
    allocate(uint256) returns(uint256) envfree
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

    assert getBucket(index) + getIncrement(index) <= getCapacity(index);
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
