/* Pure navigation rules shared by GPS, camera and smoke tests. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.RelasNavigation=api})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const angularDelta=(from,to)=>((to-from+540)%360)-180;
  function smoothHeading(previous,next,weight=.3){if(!Number.isFinite(next))return previous;if(!Number.isFinite(previous))return(next+360)%360;return(previous+angularDelta(previous,next)*weight+360)%360}
  function validFix(coords,timestamp,now=Date.now()){
    if(!coords||!Number.isFinite(coords.longitude)||!Number.isFinite(coords.latitude)||Math.abs(coords.longitude)>180||Math.abs(coords.latitude)>90)return{ok:false,reason:'Localização inválida'};
    if(!Number.isFinite(coords.accuracy)||coords.accuracy>100)return{ok:false,reason:'GPS impreciso · procure um local aberto'};
    if(!Number.isFinite(timestamp)||now-timestamp>15000||timestamp>now+5000)return{ok:false,reason:'GPS desatualizado · aguardando sinal'};
    return{ok:true};
  }
  // Speedcam convention: 0/unknown = conservative, 1 = one direction, 2 = both.
  // Preserve the raw source: an unknown vehicle heading never excludes a point.
  function directionMatches(point,heading,tolerance=55){const rule=Number(point.direction_type),direction=Number(point.direction);if(![1,2].includes(rule)||point.direction==null||point.direction===''||!Number.isFinite(direction)||!Number.isFinite(heading))return true;const delta=Math.abs(angularDelta(direction,heading));return delta<=tolerance||(rule===2&&Math.abs(delta-180)<=tolerance)}
  function smoothPosition(previous,next,weight=.6){if(!previous)return next.slice();return previous.map((v,i)=>v+(next[i]-v)*weight)}
  function cameraZoom(speed){return speed>22?15.9:speed>8?16.5:17}
  return{angularDelta,smoothHeading,validFix,directionMatches,smoothPosition,cameraZoom};
});
