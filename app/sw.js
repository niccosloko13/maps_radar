const CACHE='relas-v221-road-test';
const LOCATION=['location-parameters','geometry','baseline-engine','fix-quality','location-state-machine','motion-filter','heading-engine','candidate-corridor','route-matcher','confidence-engine','telemetry','metrics-engine','location-engine','replay-engine','debug-view'].map(name=>'/location/'+name+'.js?v=221');
const SHELL=[...LOCATION,'/','/styles.css?v=221','/boot.js?v=221','/navigation-core.js?v=221','/app.js?v=221','/icon.svg','/manifest.json','/vendor/maplibre-gl.js?v=5240','/vendor/maplibre-gl.css?v=5240',...['fixed','signal_radar','red_light','mobile','police','bump','toll','signal','other','user-chevron'].map(kind=>'/icons/'+kind+'.svg?v=221')];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('relas-')&&key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()))});
self.addEventListener('message',event=>{if(event.data?.type==='CLEAR_CACHE')event.waitUntil(caches.delete(CACHE))});
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=='GET'||url.origin!==location.origin||url.pathname.startsWith('/api/')||url.pathname.startsWith('/admin'))return;
 // Network first for HTML/bootstrap: never pin a navigation to an old release.
 // API/auth responses and external map tiles are never cached by this worker.
 const bootstrap=event.request.mode==='navigate'||['/boot.js','/sw.js','/navigation-core.js'].includes(url.pathname);
 if(bootstrap){event.respondWith(fetch(event.request,{cache:'no-cache'}).then(response=>{if(response.ok&&url.pathname!=='/sw.js'){const copy=response.clone();event.waitUntil(caches.open(CACHE).then(cache=>cache.put(event.request,copy)))}return response}).catch(()=>caches.match(event.request).then(hit=>hit||Response.error())));return}
 if(!SHELL.includes(url.pathname+url.search))return;
 event.respondWith(caches.open(CACHE).then(async cache=>{const cached=await cache.match(event.request);if(cached)return cached;const response=await fetch(event.request);if(response.ok)await cache.put(event.request,response.clone());return response}));
});
