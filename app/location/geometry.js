/* Relas Precision V2: pure modules, browser globals + CommonJS, no bundler. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory({parameters:require('./location-parameters.js')});else(root.RelasLocationModules??={}).geometry=factory(root.RelasLocationModules)})(globalThis,function(D){'use strict';

const F=D.parameters.defaults.FILTER;
const delta=(a,b)=>((b-a+540)%360)-180;
const Navigation=typeof module==='object'&&module.exports?require('../navigation-core.js'):globalThis.RelasNavigation;
const distance=Navigation.geoDistance,bearing=Navigation.geoBearing;
function frame(origin){const k=F.metresLongitude*Math.cos(origin[1]*Math.PI/180);return {to:p=>[(p[0]-origin[0])*k,(p[1]-origin[1])*F.metresLatitude],from:p=>[origin[0]+p[0]/k,origin[1]+p[1]/F.metresLatitude]}}
function project(p,s){return Navigation.projectSegment(p,s)}
function route(coordinates,P=D.parameters.defaults){const segments=[],grid=new Map(),long=[],local=frame(coordinates[0]||[0,0]);let total=0,cells=0;for(let i=1;i<coordinates.length;i++){const a=coordinates[i-1],b=coordinates[i],len=distance(a,b);if(!len)continue;const s={a,b,len,start:total,end:total+len,index:segments.length,bearing:bearing(a,b)};segments.push(s);total+=len;const x=local.to(a),y=local.to(b),c=P.MATCHER.cellMetres,bounds=[Math.floor(Math.min(x[0],y[0])/c),Math.floor(Math.min(x[1],y[1])/c),Math.floor(Math.max(x[0],y[0])/c),Math.floor(Math.max(x[1],y[1])/c)];if((bounds[2]-bounds[0]+1)*(bounds[3]-bounds[1]+1)>P.MATCHER.maxSegmentCells||cells>P.MATCHER.maxGridCells){long.push(s.index);continue}for(let u=bounds[0];u<=bounds[2];u++)for(let v=bounds[1];v<=bounds[3];v++){const key=u+','+v;if(!grid.has(key)){grid.set(key,[]);cells++}grid.get(key).push(s.index)}}return {segments,total,grid,long,local,parameters:P}}
function nearest(p,r,indices=null){let best=null;for(const s of (indices?indices.map(i=>r.segments[i]):r.segments)){const c=project(p,s);if(!best||c.distanceToRoute<best.distanceToRoute)best=c}return best}
function spatial(p,r){const c=r.parameters.MATCHER.cellMetres,n=r.parameters.MATCHER.searchCells,[x,y]=r.local.to(p),u=Math.floor(x/c),v=Math.floor(y/c),out=new Set(r.long);for(let i=u-n;i<=u+n;i++)for(let j=v-n;j<=v+n;j++)for(const k of r.grid.get(i+','+j)||[])out.add(k);return [...out]}
function range(r,start,end){let lo=0,hi=r.segments.length;while(lo<hi){const m=(lo+hi)>>1;if(r.segments[m].end<start)lo=m+1;else hi=m}const out=[];for(let i=lo;i<r.segments.length&&r.segments[i].start<=end;i++)out.push(i);return out}
return {delta,distance,bearing,frame,project,route,nearest,spatial,range};

});
