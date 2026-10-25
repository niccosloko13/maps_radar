const test=require('node:test'),assert=require('node:assert/strict');
const P=require('../app/location/location-parameters.js').defaults;
const G=require('../app/location/geometry.js');
const fix=(x=0,y=0,t=1000000,accuracy=8,extra={})=>({longitude:-46.63+x/(111320*Math.cos(-23.55*Math.PI/180)),latitude:-23.55+y/110540,timestamp:t,accuracy,speed:8,heading:90,...extra});

const Q=require('../app/location/fix-quality.js');
for(const [accuracy,score] of [[5,1],[20,.85],[80,.2]])test('accuracy score '+accuracy,()=>assert.equal(Q.evaluateFix(fix(0,0,1000000,accuracy),null,null,1000000).score,score));
for(const [name,raw,now] of [['over100',fix(0,0,1000000,101),1000000],['negative',fix(0,0,1000000,-1),1000000],['stale',fix(),1020000],['future',fix(0,0,1020000),1000000],['NaN',fix(0,0,1000000,8,{longitude:NaN}),1000000]])test('reject '+name,()=>assert.equal(Q.evaluateFix(raw,null,null,now).accepted,false));
test('duplicate and out of order',()=>{assert.equal(Q.evaluateFix(fix(),fix(),null,1000000).reasons[0],'duplicate');assert.equal(Q.evaluateFix(fix(1,0,999999),fix(),null,1000000).reasons[0],'out_of_order')});
test('outlier uses elapsed time and accuracy',()=>{assert.equal(Q.evaluateFix(fix(1000,0,1001000),fix(),null,1001000).accepted,false);assert.equal(Q.evaluateFix(fix(35,0,1001000,5,{speed:28}),fix(0,0,1000000,5,{speed:28}),{speed:28},1001000).accepted,true);assert.equal(Q.evaluateFix(fix(35,0,1001000,5,{speed:0}),fix(0,0,1000000,5,{speed:0}),{speed:0},1001000).accepted,false)});
test('raw fields are never modified',()=>{const c={coords:{...fix(),altitude:700,altitudeAccuracy:30},timestamp:1000000},copy=structuredClone(c);const raw=Q.rawFix(c);Q.evaluateFix(raw,null,null,1000000);assert.deepEqual(c,copy);assert.equal(raw.altitude,700)});
test('impossible reported speed is rejected, unknown speed remains usable',()=>{assert.equal(Q.evaluateFix(fix(0,0,1000000,8,{speed:999}),null,null,1000000).reasons[0],'invalid_speed');assert.equal(Q.evaluateFix(fix(0,0,1000000,8,{speed:null}),null,null,1000000).accepted,true)});
