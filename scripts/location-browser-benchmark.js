// Computational benchmark, not a GPS accuracy or physical-device benchmark.
async(page)=>{
 await page.goto('http://127.0.0.1:8815/?location-benchmark');
 await page.waitForFunction(()=>window.relas?.locationEngine?.snapshot);
 const cdp=await page.context().newCDPSession(page);
 await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
 try{return await page.evaluate(()=>{
  stopTracking();
  const G=RelasLocationModules.geometry,local=G.frame([-46.63,-23.55]),point=(x,y)=>local.from([x,y]);
  const coords=Array.from({length:20001},(_,i)=>point(i*5,0)),start=performance.now(),route=G.route(coords),routePreprocessingMs=performance.now()-start,cases=[];
  for(const recording of [false,true]){
   const engine=RelasLocationModules.engine.create(),times=[];
   if(recording)engine.telemetry.start({route:{geometry:{coordinates:coords}}});
   for(let i=0;i<600;i++){
    const p=point(i*8,Math.sin(i*3)*2),raw={longitude:p[0],latitude:p[1],accuracy:8,speed:8,heading:90,timestamp:1000000+i*1000},t=performance.now();
    engine.process(raw,{route:{geometry:{coordinates:coords}},routeIndex:route,now:raw.timestamp});times.push(performance.now()-t);
   }
   const sorted=times.slice(5).sort((a,b)=>a-b);
   if(recording&&engine.telemetry.size!==600)throw Error('Telemetry stopped before performance run finished');
   cases.push({recording,medianMs:sorted[Math.floor(sorted.length*.5)],p95Ms:sorted[Math.ceil(sorted.length*.95)-1],coldMs:times[0],lastExamined:engine.lastResult.examined,records:engine.telemetry.size,routeContexts:engine.telemetry.contexts.length});
  }
  return {browser:navigator.userAgent,cpuThrottle:4,synthetic:true,segments:20000,fixesPerCase:600,routePreprocessingMs,cases,physicalAccuracyMeasured:false};
 })}finally{await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});await cdp.detach()}
}
