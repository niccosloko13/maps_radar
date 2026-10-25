// Relas road-test runtime: versioned shell and local MapLibre fallback.
(() => {
  const VERSION = '5.24.0';
  const cssSources = [
    '/vendor/maplibre-gl.css?v=5240',
    `https://unpkg.com/maplibre-gl@${VERSION}/dist/maplibre-gl.css`,
    `https://cdn.jsdelivr.net/npm/maplibre-gl@${VERSION}/dist/maplibre-gl.css`
  ];
  const jsSources = [
    '/vendor/maplibre-gl.js?v=5240',
    `https://unpkg.com/maplibre-gl@${VERSION}/dist/maplibre-gl.js`,
    `https://cdn.jsdelivr.net/npm/maplibre-gl@${VERSION}/dist/maplibre-gl.js`
  ];
  function loadCss(i=0){
    if(i>=cssSources.length) return;
    const l=document.createElement('link'); l.rel='stylesheet'; l.href=cssSources[i];
    l.onerror=()=>{l.remove();loadCss(i+1)}; document.head.appendChild(l);
  }
  function loadScript(i=0){
    if(window.maplibregl) return Promise.resolve();
    if(i>=jsSources.length) return Promise.reject(new Error('MapLibre indisponÃ­vel nas fontes local e CDN'));
    return new Promise((resolve,reject)=>{
      const s=document.createElement('script'); s.src=jsSources[i]; s.async=false;
      s.onload=()=> window.maplibregl ? resolve() : reject(new Error('MapLibre carregou sem expor maplibregl'));
      s.onerror=()=>{s.remove(); loadScript(i+1).then(resolve,reject)};
      document.head.appendChild(s);
    }).catch(()=>loadScript(i+1));
  }
  function loadLocationModules(){const names=['location-parameters','geometry','baseline-engine','fix-quality','location-state-machine','motion-filter','heading-engine','candidate-corridor','route-matcher','confidence-engine','telemetry','metrics-engine','location-engine','replay-engine','debug-view'];return names.reduce((promise,name)=>promise.then(()=>new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/location/'+name+'.js?v=221';script.onload=resolve;script.onerror=()=>reject(Error('Location module unavailable: '+name));document.head.append(script)})),Promise.resolve()).catch(()=>{window.relasLocationLoadError=true;console.warn('Relas location modules unavailable; baseline active')})}
  function loadApp(){
    const s=document.createElement('script'); s.src='/app.js?v=221'; document.body.appendChild(s);
  }
  function fatal(err){
    document.body.innerHTML=`<main style="min-height:100vh;background:#07110d;color:#fff;display:grid;place-items:center;font-family:system-ui;padding:28px"><div style="max-width:680px;text-align:center"><h2>Mapa indisponÃ­vel</h2><p>${String(err&&err.message||err)}</p><p style="opacity:.7">Abra <b>/api/vendor/status</b> para diagnÃ³stico. A base local de radares continua preservada.</p></div></main>`;
  }
  loadCss();
  loadScript().then(()=>new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/navigation-core.js?v=221';script.onload=resolve;script.onerror=()=>reject(Error('Não foi possível carregar a navegação'));document.head.append(script)})).then(loadLocationModules).then(loadApp).catch(fatal);
  if('serviceWorker' in navigator&&window.isSecureContext){
    let controlled=Boolean(navigator.serviceWorker.controller),refreshing=false;
    navigator.serviceWorker.addEventListener('controllerchange',()=>{if(controlled&&!refreshing){if(window.relas?.state.driving){window.relas.state.pendingUpdate=true;return}refreshing=true;location.reload()}controlled=true});
    window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js',{updateViaCache:'none'}).then(reg=>reg.update()).catch(error=>console.warn('Cache indisponível:',error.message)));
  }
})();
