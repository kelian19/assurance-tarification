import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {predictProfile} from '../dist/model.mjs';
import {calculate} from '../dist/engine.mjs';
const model=JSON.parse(readFileSync(new URL('../artifacts/model.json',import.meta.url)));
const fixtures=JSON.parse(readFileSync(new URL('profile_fixtures.json',import.meta.url)));
for(const item of fixtures){
 const result=predictProfile(item.profile,model);
 for(const key of ['frequency','severity','beta','k','prior'])assert.ok(Math.abs(result[key]/item.prediction[key]-1)<1e-10,`${key}: export mismatch`);
 const base=calculate({...result,history:[]});assert.ok(Math.abs(base.annualPure/result.prior-1)<1e-10);
 const adjusted=calculate({...result,history:Array(3).fill({exposure:1,claims:0,amount:0})});assert.ok(adjusted.bayes<result.prior&&adjusted.bayes>0);
}
assert.throws(()=>predictProfile({...fixtures[0].profile,Region:'unknown'},model));
assert.throws(()=>predictProfile({...fixtures[0].profile,DrivAge:17},model));
assert.throws(()=>predictProfile(fixtures[0].profile,model,0));
console.log(`Parité GLM calibré Python / navigateur : ${fixtures.length} profils, contrôles de domaine et posterior validés.`);
