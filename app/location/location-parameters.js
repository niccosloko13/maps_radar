/* Relas Precision V2: pure modules, browser globals + CommonJS, no bundler. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory({});else(root.RelasLocationModules??={}).parameters=factory(root.RelasLocationModules)})(globalThis,function(D){'use strict';

const defaults={
 VERSION:'2.0.0',
 BASELINE:{maxJumpSpeed:70,maxJumpGap:15,derivedMinDt:.5,derivedMaxDt:10,derivedMinTravel:5,accuracyFactor:.3,headingTravel:8,headingWeight:.4},
 QUALITY:{accuracyScores:[[5,1],[10,.95],[20,.85],[35,.70],[50,.55],[75,.35],[100,.20]],maxAccuracy:100,maxAgeMs:15000,futureMs:5000,maxSpeed:70,maxAcceleration:12,innovationSigma:4,uncertaintyFactor:2,minDt:.2,gapResetSeconds:15,outlierFloor:18,innovationPenalty:.5,frequencyPenalty:.8,headingPenalty:.8},
 FILTER:{metresLatitude:110540,metresLongitude:111320,minimumSigma:3,accuracyToSigma:.5,initialVelocityVariance:100,reinitializeGap:12,stationarySpeed:.8,lowSpeed:3,highSpeed:22,turnDegrees:25,stationaryDamping:.25,profiles:{STATIONARY:.2,LOW_SPEED:1,URBAN:3,HIGH_SPEED:5,TURNING:10,GPS_DEGRADED:4}},
 HEADING:{movingSpeed:1.2,minDisplacement:4,gpsGoodAccuracy:35,lowWeight:.2,highWeight:.65,turnWeight:.85,turnDegrees:30,routeWeight:.12,velocityMin:1.2,maxVelocityVariance:100,contradictionDegrees:100},
 STATE_MACHINE:{acquireFixes:3,badFixes:2,recoverFixes:3,goodScore:.65,regularGapSeconds:3,predictAfterMs:1000},
 MATCHER:{cellMetres:150,maxGridCells:50000,maxSegmentCells:400,searchCells:2,behind:150,ahead:1000,stationaryAhead:180,lookaheadSeconds:20,degradedExpansion:1.5,expandedFactor:3,maxDistance:110,minimumSigma:8,topK:5,headingWeight:3,progressWeight:.4,backwardWeight:2,jumpWeight:.7,predictionWeight:.25,continuityWeight:.15,plausibleProgressFloor:30,headingMovingSpeed:1.2,outputReuseMetres:3,maxOppositeDegrees:125,maxScore:15,scoreDecay:4,separationFloor:.5,separationWeight:.5},
 HYSTERESIS:{MATCH_SWITCH_MARGIN:.6,MATCH_SWITCH_CONFIRMATIONS:3,MATCH_HARD_RESET_DISTANCE:120,strongMargin:4,adjacentAlong:40},
 PREDICTION:{strongMs:2000,maxMs:5000,confidenceDecayMs:3000,minimumConfidence:.35},
 CONFIDENCE:{excellent:.9,good:.75,fair:.55,weak:.35,covarianceScale:60,acquiringCap:.6,degradedCap:.54,ageDecayMs:15000,blendStart:.55,blendEnd:.9,blendWeightStep:.2,unknownHeadingWeight:.5,noMatchWeight:.5,weights:{quality:.4,covariance:.2,history:.2,heading:.1,match:.1}},
 PERFORMANCE:{medianBudgetMs:5,p95BudgetMs:15,telemetryCapacity:3000,maxRouteContexts:16,sessionLimitMs:3600000,debugCirclePoints:32,heartbeatMs:500,diagnosticCapacity:20}
};
function freeze(o){Object.values(o).forEach(v=>{if(v&&typeof v==='object')freeze(v)});return Object.freeze(o)}
function create(overrides={}){function merge(a,b){const o={...a};for(const k in b){if(!(k in a))throw Error('Unknown location parameter '+k);o[k]=b[k]&&typeof b[k]==='object'&&!Array.isArray(b[k])?merge(a[k],b[k]):b[k]}return o}const merged=merge(defaults,structuredClone(overrides));function validate(o){for(const [k,v] of Object.entries(o)){if(v&&typeof v==='object')validate(v);else if(typeof v==='number'&&(!Number.isFinite(v)||v<0))throw Error('Invalid location parameter '+k)}}validate(merged);if(merged.PERFORMANCE.telemetryCapacity<1||!Number.isInteger(merged.PERFORMANCE.telemetryCapacity))throw Error('Invalid telemetry capacity');return freeze(merged)}
return {defaults:freeze(defaults),create};

});
