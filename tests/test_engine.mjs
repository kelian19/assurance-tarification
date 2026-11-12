import assert from 'node:assert/strict';
import {calculate} from '../dist/engine.mjs';
const base={frequency:.08,severity:2500};
assert.equal(calculate(base).annualPure,200);
assert.ok(Math.abs(calculate({...base,history:Array(3).fill({exposure:1,claims:0,amount:0})}).bayes-800/7)<1e-10);
assert.throws(()=>calculate({...base,history:[{exposure:0,claims:1,amount:100}]}));
assert.throws(()=>calculate({...base,expenseRate:.8,marginRate:.3}));
assert.throws(()=>calculate({...base,history:[{exposure:1,claims:0,amount:100}]}));
console.log('JavaScript: invariants actuariels validés.');
