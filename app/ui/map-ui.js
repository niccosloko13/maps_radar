/* Relas UI V3: presentation only; no persistence or navigation decisions. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.RelasUI=factory()})(globalThis,()=>{
 'use strict';
 const paths={search:'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',layers:'M12 3l10 6-10 6L2 9zM3 13l9 5 9-5M3 17l9 5 9-5',locate:'M12 2v4m0 12v4M2 12h4m12 0h4M18 12a6 6 0 1 1-12 0 6 6 0 0 1 12 0',recenter:'M3 8V3h5m8 0h5v5m0 8v5h-5M8 21H3v-5M12 7l4 9-4-2-4 2z',plus:'M12 5v14M5 12h14',minus:'M5 12h14',close:'M6 6l12 12M6 18L18 6',route:'M5 20V8a4 4 0 0 1 4-4h10m-4-3 4 3-4 3M3 20h4',voice:'M3 9h4l5-4v14l-5-4H3zM16 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14',mute:'M3 9h4l5-4v14l-5-4H3zM16 9l6 6m0-6-6 6',simulate:'M8 4l12 8-12 8z',theme:'M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10',chevron:'M9 5l7 7-7 7',up:'M5 14l7-7 7 7',down:'M5 9l7 7 7-7',filter:'M3 5h18M6 12h12M9 19h6',straight:'M12 21V3M5 10l7-7 7 7',left:'M17 21V9H4m6-6L4 9l6 6',right:'M7 21V9h13m-6-6 6 6-6 6'};
 function icon(name){return '<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+(paths[name]||paths.layers)+'"/></svg>'}
 const categories={fixed:'Radares fixos',signal_radar:'Radares semafóricos',red_light:'Câmeras de avanço',mobile:'Radares móveis',police:'Fiscalização',bump:'Lombadas',toll:'Pedágios',signal:'Semáforos',accident:'Acidentes',works:'Obras',other:'Outros alertas'};
 const reportIcons={stopped:'stopped',obstacle:'other',congestion:'congestion',flood:'rain',pothole:'bump',broken_signal:'signal'};
 function kind(p){return p.report_kind==='works'?'works':p.report_kind==='accident'?'accident':(p.kind in categories?p.kind:'other')}
 function iconFor(p){return reportIcons[p.report_kind]||kind(p)}
 function normalize(f){const p={...f.properties};p.display_kind=kind(p);p.display_icon=iconFor(p);return {...f,properties:p}}
 function visible(f,enabled,community=true){return enabled.has(kind(f.properties))&&(community||f.properties.source!=='public_report')}
 function counts(features){const c={};for(const f of features){const k=kind(f.properties);c[k]=(c[k]||0)+1}return c}
 return {icon,categories,kind,iconFor,normalize,visible,counts};
});
