// Isolated frontend on localhost:8815. Positions are synthetic; no report is submitted.
async(page)=>{
 const result={errors:[],expectedDiagnostics:0},check=(ok,message)=>{if(!ok)throw Error(message)};
 page.on('pageerror',e=>result.errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error'&&m.text().includes('baseline fallback active'))result.expectedDiagnostics++});
 await page.context().grantPermissions(['geolocation'],{origin:'http://127.0.0.1:8815'});
 await page.context().setGeolocation({longitude:-46.655,latitude:-23.563,accuracy:8});
 await page.setViewportSize({width:390,height:844});
 await page.goto('http://127.0.0.1:8815/?v=221');
 await page.waitForFunction(()=>window.relas?.locationEngine&&relas.state.position&&relas.state.features.length>0);
 await page.evaluate(()=>{stopTracking();relas.state.follow=false;localStorage.removeItem('relas-location-debug');relas.setLocationMode('baseline')});
 result.defaults=await page.evaluate(()=>({mode:relas.state.locationMode,telemetryActive:relas.locationEngine.telemetry.active,debug:!!document.querySelector('#locationDebug')}));
 check(!result.defaults.telemetryActive&&!result.defaults.debug,'Debug/telemetry must start off');
 result.gps=await page.evaluate(async()=>{
  await relas.setRoute({geometry:{type:'LineString',coordinates:[[-46.656,-23.563],[-46.64,-23.563]]},distance_m:1600,duration_s:180,steps:[{instruction:'Siga pela avenida',distance:1600}],alerts:[],alerts_engine:'relas-map-v2'});
  relas.startDrive(false);stopTracking();relas.state.follow=false;relas.setLocationMode('v2');relas.locationTelemetry.start();
  const states=[],t=Date.now()-4000;window.precisionLastAt=t+3000;
  for(let i=0;i<4;i++){relas.receivePosition({timestamp:t+i*1000,coords:{longitude:-46.655+i*.00008,latitude:-23.563,accuracy:8,speed:8,heading:90,altitude:700,altitudeAccuracy:30}});states.push(relas.state.locationState)}
  return {states,confidence:relas.state.locationConfidence,rawAccuracy:relas.state.accuracy,match:relas.state.routeMatch?.source,rawAltitude:relas.state.locationResult.raw.altitude};
 });
 check(result.gps.states.join(',')==='ACQUIRING,ACQUIRING,TRACKING,TRACKING','Acquisition sequence failed');
 check(result.gps.match==='local-route-v2','Route matcher not consumed by app');
 await page.evaluate(()=>{localStorage.setItem('relas-location-debug','1');relas.receivePosition({timestamp:precisionLastAt+500,coords:{longitude:-46.65472,latitude:-23.563,accuracy:8,speed:8,heading:90}});precisionLastAt+=500});
 await page.waitForTimeout(500);
 result.debug=await page.evaluate(()=>({panel:!!document.querySelector('#locationDebug'),rawLayer:!!relas.map.getLayer('location-debug-raw'),candidates:!!relas.map.getLayer('location-debug-lines')}));
 check(result.debug.panel&&result.debug.rawLayer&&result.debug.candidates,'Debug layers missing');
 await page.screenshot({path:'artifacts/location-precision-v2/debug-mobile.png'});
 result.gap=await page.evaluate(()=>{
  relas.state.watch=999;relas.locationTick(precisionLastAt+2500);
  const predicted={state:relas.state.locationState,confidence:relas.state.locationConfidence,visibleAlert:!document.querySelector('#nextAlert').hidden};
  relas.locationTick(precisionLastAt+6500);
  const lost={state:relas.state.locationState,speed:relas.state.speed,position:relas.state.position.slice()};relas.state.watch=null;return {predicted,lost};
 });
 check(result.gap.predicted.state==='PREDICTING'&&!result.gap.predicted.visibleAlert&&result.gap.lost.state==='LOST'&&result.gap.lost.speed===null,'Bounded prediction failed');
 await page.waitForTimeout(6500);
 result.recovery=await page.evaluate(()=>{
  relas.receivePosition({timestamp:Date.now(),coords:{longitude:-46.65465,latitude:-23.563,accuracy:8,speed:0,heading:null}});
  relas.locationTelemetry.stop();window.precisionSession=relas.locationTelemetry.exportJSON();
  return {state:relas.state.locationState,confidence:relas.state.locationConfidence,records:JSON.parse(precisionSession).records.length};
 });
 check(result.recovery.state==='ACQUIRING'&&result.recovery.confidence<=.6,'Recovery skipped acquisition');
 result.replay=await page.evaluate(()=>{
  const a=new RelasLocationModules.replay.Replay().load(precisionSession).setSpeed('instant').play(),b=new RelasLocationModules.replay.Replay().load(precisionSession).setSpeed('instant').play();
  RelasLocationReplay.load(precisionSession).setSpeed('instant').play();RelasLocationReplay.pause();RelasLocationReplay.seek(2);RelasLocationReplay.step();
  return {deterministic:JSON.stringify(a.results)===JSON.stringify(b.results),metrics:a.metrics(),visualActive:relas.state.locationReplayActive,step:RelasLocationReplay.index};
 });
 check(result.replay.deterministic&&result.replay.visualActive&&result.replay.step===3,'Replay failed');
 await page.screenshot({path:'artifacts/location-precision-v2/replay-mobile.png'});
 result.fallback=await page.evaluate(()=>{
  relas.exitLocationReplay();stopTracking();relas.setLocationMode('v2');const engine=relas.locationEngine,original=engine.process;
  engine.process=()=>{throw new Error('Intentional smoke failure')};
  relas.receivePosition({timestamp:Date.now(),coords:{longitude:-46.65465,latitude:-23.563,accuracy:8,speed:0,heading:null}});engine.process=original;
  const out={state:relas.state.locationState,position:!!relas.state.position,diagnostics:relas.state.locationDiagnostics.length};
  relas.setLocationMode('baseline');localStorage.removeItem('relas-location-debug');relas.locationEngine.telemetry.clear();return out;
 });
 check(result.fallback.state==='BASELINE_FALLBACK'&&result.fallback.position&&result.fallback.diagnostics>0,'Fallback did not preserve navigation');
 const fallbackContext=await page.context().browser().newContext({serviceWorkers:'block',permissions:['geolocation'],geolocation:{longitude:-46.655,latitude:-23.563,accuracy:8}}),fallback=await fallbackContext.newPage(),bootstrapErrors=[];
 fallback.on('pageerror',e=>bootstrapErrors.push(e.message));
 await fallback.route('**/location/motion-filter.js*',r=>r.fulfill({status:404,body:''}));
 await fallback.goto('http://127.0.0.1:8815/?bootstrap-fallback');await fallback.waitForFunction(()=>window.relas?.state.position);
 result.bootstrapFallback={working:await fallback.evaluate(()=>relas.state.locationMode==='baseline'&&!!relas.state.position),loadFailureObserved:await fallback.evaluate(()=>window.relasLocationLoadError===true&&window.RelasLocation===undefined),errors:bootstrapErrors};
 await fallbackContext.close();check(result.bootstrapFallback.working&&result.bootstrapFallback.loadFailureObserved&&bootstrapErrors.length===0,'Module bootstrap failure killed baseline');
 check(result.errors.length===0,'Unexpected JavaScript error');return result;
}
