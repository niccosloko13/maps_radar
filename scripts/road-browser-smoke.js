// Execute with the connected Playwright tool (filename), or use the exported
// function through the standalone runner in scripts/run-road-browser.cjs.
async (page) => {
  const result={viewports:[],types:{},consoleErrors:[],httpErrors:[]};
  page.on('pageerror',error=>result.consoleErrors.push(error.message));
  page.on('response',response=>{if(response.status()>=400)result.httpErrors.push({url:response.url(),status:response.status()})});
  const check=(ok,message)=>{if(!ok)throw Error(message)};
  await page.context().grantPermissions(['geolocation'],{origin:'http://127.0.0.1:8815'});
  await page.context().setGeolocation({longitude:-46.655,latitude:-23.563,accuracy:8});
  await page.setViewportSize({width:390,height:844});
  await page.goto('http://127.0.0.1:8815/?v=220');
 await page.waitForLoadState('networkidle');
  await page.waitForFunction(()=>window.relas?.map.getSource('relas-signals')&&relas.state.features.length>0);
  await page.waitForFunction(()=>relas.state.watch!==null&&relas.state.position!==null);
  result.gpsStart=await page.evaluate(()=>({watch:relas.state.watch!==null,status:document.querySelector('#gpsIndicator').textContent,position:!!relas.state.position}));
  await page.evaluate(()=>{relas.state.follow=false;stopTracking()});
  const all=await page.evaluate(async()=>{const r=await fetch('/api/map/features?bbox=-53.2,-25.4,-44,-19.7');return(await r.json()).features});
  async function settlePoint(feature,zoom=14){
    await page.evaluate(({p,zoom})=>{relas.state.follow=false;relas.map.jumpTo({center:p,zoom})},{p:feature.geometry.coordinates,zoom});
    await page.waitForFunction(id=>relas.state.features.some(f=>f.properties.id===id),feature.properties.id);
    await page.waitForTimeout(600);
  }
  for(const kind of ['signal','fixed','signal_radar','red_light','mobile','police','bump','toll']){
    const feature=kind==='signal'?all.find(f=>f.properties.kind===kind&&Math.abs(f.geometry.coordinates[0]+46.655)<.002&&Math.abs(f.geometry.coordinates[1]+23.563)<.002):[...all.filter(f=>f.properties.kind===kind&&f.properties.municipality==='São Bernardo do Campo'),...all.filter(f=>f.properties.kind===kind)].find(f=>all.every(o=>o.properties.kind==='signal'||o.properties.kind===kind||Math.hypot((o.geometry.coordinates[0]-f.geometry.coordinates[0])*.92,o.geometry.coordinates[1]-f.geometry.coordinates[1])>.0005))||all.find(f=>f.properties.kind===kind);
    check(feature,'No feature for '+kind);await settlePoint(feature);
    const metrics=await page.evaluate(async kind=>{
      const b=relas.map.getBounds(),bbox=[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].join(','),start=performance.now(),response=await fetch('/api/map/features?bbox='+bbox+'&types='+kind),fc=await response.json(),ids=new Set(fc.features.map(f=>f.properties.id));
      const layer=kind==='signal'?'relas-signal-icons':'relas-icons',source=kind==='signal'?'relas-signals':'relas-points',raw=await relas.map.getSource(source).getData(),rendered=relas.map.queryRenderedFeatures({layers:[layer]}).filter(f=>f.properties.kind===kind&&ids.has(f.properties.id));
      const other=relas.map.queryRenderedFeatures({layers:['relas-icons']}).filter(f=>f.properties.kind!=='signal');
      const candidates=rendered.map(f=>({id:f.properties.id,p:relas.map.project(f.geometry.coordinates)})).filter(f=>f.p.x>65&&f.p.x<innerWidth-65&&f.p.y>225&&f.p.y<innerHeight-170&&(kind!=='signal'||other.every(o=>{const q=relas.map.project(o.geometry.coordinates);return Math.hypot(q.x-f.p.x,q.y-f.p.y)>26}))).sort((a,b)=>Math.hypot(a.p.x-innerWidth/2,a.p.y-innerHeight/2)-Math.hypot(b.p.x-innerWidth/2,b.p.y-innerHeight/2));
      return{bbox,zoom:relas.map.getZoom(),status:response.status,api:fc.features.length,source:raw.features.filter(f=>f.properties.kind===kind).length,rendered:new Set(rendered.map(f=>f.properties.id)).size,icon:relas.map.hasImage(kind),layer,sourceId:source,minzoom:relas.map.getLayer(layer).minzoom||0,queryMs:performance.now()-start,target:candidates[0]||null};
    },kind);
    check(metrics.status===200&&metrics.api>0&&metrics.rendered>0&&metrics.icon,'Rendering failed '+kind+' '+JSON.stringify(metrics));check(metrics.target,'No unobscured touch candidate '+kind);
    await page.mouse.click(metrics.target.p.x,metrics.target.p.y);await page.waitForSelector('#sheet[open]');metrics.detail=await page.locator('#sheetContent h2').innerText();
    const expected={signal:'Semáforo',fixed:'Radar fixo',signal_radar:'Radar semafórico',red_light:'Câmera de avanço',mobile:'Radar móvel',police:'Fiscalização',bump:'Lombada',toll:'Pedágio'};
    check(metrics.detail===expected[kind],'Wrong point detail: '+kind+' -> '+metrics.detail);
    if(['signal','fixed','bump'].includes(kind))await page.screenshot({path:'artifacts/road-test-review/detail-'+kind+'.png'});
    await page.locator('#closeSheet').click();delete metrics.target;result.types[kind]=metrics;
  }
  // Dedicated semaphore region, same zoom/viewport as the initial audit.
  await page.evaluate(()=>relas.map.jumpTo({center:[-46.655,-23.563],zoom:14}));await page.waitForTimeout(1100);
  result.semaphores=await page.evaluate(async()=>{const b=relas.map.getBounds(),bbox=[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].join(','),api=await(await fetch('/api/map/features?bbox='+bbox+'&types=signal')).json(),ids=new Set(api.features.map(f=>f.properties.id));return{bbox,api:api.features.length,source:(await relas.map.getSource('relas-signals').getData()).features.length,rendered:new Set(relas.map.queryRenderedFeatures({layers:['relas-signal-icons']}).filter(f=>ids.has(f.properties.id)).map(f=>f.properties.id)).size}});
  await page.screenshot({path:'artifacts/road-test-review/semaforos-map.png'});
  await page.locator('#layersBtn').click();check(await page.locator('[data-layer]').count()===9,'Layer controls missing');await page.locator('[data-layer="signal"]').uncheck();await page.locator('#closeSheet').click();await page.waitForFunction(async()=>(await relas.map.getSource('relas-signals').getData()).features.length===0);
  result.signalFilterOff=true;
  await page.reload();await page.waitForFunction(()=>window.relas?.map.getSource('relas-signals'));check(await page.evaluate(()=>!relas.state.enabled.has('signal')),'Layer setting did not persist');
  await page.locator('#layersBtn').click();await page.locator('[data-layer="signal"]').check();await page.screenshot({path:'artifacts/road-test-review/filters.png'});await page.locator('#closeSheet').click();
  for(const viewport of [{width:375,height:812},{width:390,height:844},{width:430,height:932},{width:412,height:915}]){
    await page.setViewportSize(viewport);await page.waitForTimeout(250);const mobile=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,smallButtons:[...document.querySelectorAll('button')].filter(b=>b.getClientRects().length&&getComputedStyle(b).visibility!=='hidden').filter(b=>{const r=b.getBoundingClientRect();return r.height<44||r.width<44}).map(b=>b.id||b.className)}));
    check(!mobile.overflow&&mobile.smallButtons.length===0,'Mobile touch target/overflow '+JSON.stringify(mobile));result.viewports.push({...viewport,...mobile});await page.screenshot({path:'artifacts/road-test-review/mobile-'+viewport.width+'.png'});
  }
  await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>{relas.state.follow=false;relas.map.jumpTo({center:[-46.655,-23.563],zoom:14})});await page.waitForTimeout(700);await page.screenshot({path:'artifacts/road-test-review/desktop-map.png'});
  result.domMarkers=await page.locator('.maplibregl-marker').count();check(result.domMarkers===0,'DOM markers found');
  result.frames=await page.evaluate(()=>new Promise(resolve=>{const intervals=[],start=performance.now();let last=start;relas.map.easeTo({center:[-46.653,-23.561],duration:1600});function frame(now){intervals.push(now-last);last=now;if(now-start<2000)requestAnimationFrame(frame);else{const sorted=intervals.slice(2).sort((a,b)=>a-b);resolve({frames:intervals.length,durationMs:now-start,averageFps:Math.round(1000*intervals.length/(now-start)),p95FrameMs:sorted[Math.floor(sorted.length*.95)]})}}requestAnimationFrame(frame)}));
  check(result.gpsStart.watch&&result.gpsStart.position,'GPS startup failed');check(result.consoleErrors.length===0,'JS error(s): '+result.consoleErrors.join(';'));return result;
}
