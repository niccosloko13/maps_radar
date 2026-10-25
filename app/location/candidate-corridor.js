/* Relas Precision V2: pure modules, browser globals + CommonJS, no bundler. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory({parameters:require('./location-parameters.js'),geometry:require('./geometry.js')});else(root.RelasLocationModules??={}).corridor=factory(root.RelasLocationModules)})(globalThis,function(D){'use strict';

function candidates(route,position,previous,speed,dt,degraded,P=D.parameters.defaults,expanded=false){const M=P.MATCHER,factor=(degraded?M.degradedExpansion:1)*(expanded?M.expandedFactor:1);if(!previous)return {indices:D.geometry.spatial(position,route),start:0,end:route.total,expanded};const ahead=(speed<P.HEADING.movingSpeed?M.stationaryAhead:M.ahead+speed*Math.max(dt,M.lookaheadSeconds))*factor,start=Math.max(0,previous.along-M.behind*factor),end=Math.min(route.total,previous.along+ahead);return {indices:D.geometry.range(route,start,end),start,end,expanded}}
return {candidates};

});
