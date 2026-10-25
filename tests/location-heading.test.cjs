const test=require('node:test'),assert=require('node:assert/strict');
const P=require('../app/location/location-parameters.js').defaults;
const G=require('../app/location/geometry.js');
const fix=(x=0,y=0,t=1000000,accuracy=8,extra={})=>({longitude:-46.63+x/(111320*Math.cos(-23.55*Math.PI/180)),latitude:-23.55+y/110540,timestamp:t,accuracy,speed:8,heading:90,...extra});

const {HeadingEngine}=require('../app/location/heading-engine.js');const est=(x=0,y=0)=>({...fix(x,y),velocityEast:8,velocityNorth:0,speed:8});
for(const [a,b] of [[359,1],[1,359]])test('wrap '+a+' to '+b,()=>{const e=new HeadingEngine();e.update(fix(0,0,1000000,8,{heading:a}),est());const out=e.update(fix(8,0,1001000,8,{heading:b}),est(8));assert.ok(Math.abs(G.delta(a,out.heading))<3)});
test('stationary GPS heading is ignored',()=>{const e=new HeadingEngine();assert.equal(e.update(fix(0,0,1000000,5,{speed:0,heading:123}),{...est(),speed:0}).heading,null)});
test('missing heading derives from filtered movement',()=>{const e=new HeadingEngine();e.update(fix(0,0,1000000,8,{heading:null}),{...est(),speed:0});const out=e.update(fix(8,0,1001000,8,{heading:null}),est(8));assert.equal(out.source,'motion');assert.ok(Math.abs(out.heading-90)<1)});
test('low speed ignores GPS, turn responds with less lag',()=>{const e=new HeadingEngine();e.update(fix(),est());const turn=e.update(fix(8,0,1001000,5,{heading:0}),est(8));assert.ok(turn.heading<30);const low=e.update(fix(8,0,1002000,5,{heading:180,speed:.5}),{...est(8),speed:.5});assert.equal(low.source,'previous')});
test('contradictory GPS heading loses priority to coherent filtered motion',()=>{const {LocationEngine}=require('../app/location/location-engine.js'),e=new LocationEngine();let result;for(let i=0;i<15;i++)result=e.process(fix(i*8,0,1000000+i*1000,8,{heading:270}));assert.ok(Math.abs(G.delta(90,result.output.heading))<10);assert.ok(result.quality.reasons.includes('heading_inconsistent'));assert.equal(result.state,'DEGRADED')});
