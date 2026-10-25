/* Relas Precision V2: pure modules, browser globals + CommonJS, no bundler. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory({parameters:require('./location-parameters.js')});else(root.RelasLocationModules??={}).confidence=factory(root.RelasLocationModules)})(globalThis,function(D){'use strict';

function level(value,P=D.parameters.defaults){const C=P.CONFIDENCE;return value>=C.excellent?'excellent':value>=C.good?'good':value>=C.fair?'fair':value>=C.weak?'weak':'poor'}
function confidence(quality,estimated,state,history,heading,matched,age=0,P=D.parameters.defaults){const C=P.CONFIDENCE,w=C.weights,covariance=Math.sqrt(Math.max(0,estimated.covariance[0][0]+estimated.covariance[1][1]));let score=quality.score*w.quality+Math.exp(-covariance/C.covarianceScale)*w.covariance+Math.min(1,history/P.STATE_MACHINE.acquireFixes)*w.history+(heading.source==='gps'||heading.source==='motion'?1:C.unknownHeadingWeight)*w.heading+(matched?matched.confidence:C.noMatchWeight)*w.match;score*=Math.exp(-Math.max(0,age)/C.ageDecayMs);if(state==='ACQUIRING')score=Math.min(C.acquiringCap,score);if(state==='DEGRADED')score=Math.min(C.degradedCap,score);if(state==='LOST'||state==='INITIALIZING')score=0;return Math.max(0,Math.min(1,score))}
return {confidence,level};

});
