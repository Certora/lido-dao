methods { }


// need to understand syste more to resolve calls, however, they are just NONDET, so no need to resolve them until they cause false violations 
// https://vaas-stg.certora.com/output/3106/3ad7d13c5d9f4196b9404ded723b9574/?anonymousKey=2c3653b2ce52320bbc0d21755f08d78796a5f69c
rule sanity(env e, method f) {
    calldataarg args;
    f(e, args);
    assert false;
}


