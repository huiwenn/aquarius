import maplibregl from 'https://unpkg.com/maplibre-gl@5.6.2/dist/maplibre-gl.js';

const [geoResponse, dataResponse] = await Promise.all([fetch('./provinces.geojson'), fetch('./data.json')]);
if (!geoResponse.ok || !dataResponse.ok) throw new Error('Map data could not be loaded. Run build_data.py and serve this folder over HTTP.');
const geo = await geoResponse.json();
const data = await dataResponse.json();
const counts = new Map(data.features.map(x => [x.province, x.count]));
geo.features = geo.features.filter(f => /^\d{6}$/.test(String(f.properties?.code)) && Number(f.properties.code) % 10000 === 0);
geo.features.forEach(f => { f.properties.record_count = counts.get(f.properties.name) || 0; });
const byProvince = new Map(data.provinces.map(x => [x.province, x]));

const map = new maplibregl.Map({
  container: 'map',
  style: {version:8, sources:{}, layers:[{id:'paper',type:'background',paint:{'background-color':'#ebeae2'}}]},
  center:[103,36], zoom:2.6, minZoom:2, maxZoom:8, maxBounds:[[73,15],[135,55]],
  attributionControl:false
});
map.addControl(new maplibregl.NavigationControl({showCompass:false}), 'bottom-right');
map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:'Boundary data: Tianditu · GeoJSON.cn'}));
let selected = '';
const select = document.querySelector('#provinceSelect');
for (const p of [...data.provinces].sort((a,b)=>a.province.localeCompare(b.province,'zh'))) {
  const o=document.createElement('option'); o.value=p.province; o.textContent=`${p.province} · ${p.count}`; select.append(o);
}

function show(name) {
  const p = byProvince.get(name); if (!p) return;
  const maxRegion=Math.max(...p.regions.map(r=>r.count),1);
  const maxSongs=12;
  document.querySelector('#details').innerHTML=`<h2 class="province-title">${escapeHTML(p.province)}</h2><div class="province-count">${p.count} recordings · ${p.regions.length} cultural region${p.regions.length===1?'':'s'}</div><div class="region-heading">CULTURAL REGION MIX</div>${p.regions.map(r=>`<div class="region-row"><div>${escapeHTML(r.name)}<div class="bar"><span style="width:${Math.round(r.count/maxRegion*100)}%"></span></div></div><b>${r.count}</b></div>`).join('')}<div class="region-heading">RECORDINGS FROM THIS PROVINCE</div><div class="song-list">${p.songs.slice(0,maxSongs).map(s=>`<article class="song"><a href="${safeURL(s.url)}" target="_blank" rel="noreferrer">${escapeHTML(s.title||s.videoTitle||'Untitled recording')} ↗</a><div class="song-meta">${[s.region,s.place,s.genre,s.ethnicGroup].filter(Boolean).map(escapeHTML).join(' · ')}</div></article>`).join('')}</div>${p.songs.length>maxSongs?`<div class="more">Showing ${maxSongs} of ${p.songs.length} recordings</div>`:''}`;
}
function escapeHTML(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function safeURL(x){try{const u=new URL(x);return ['https:'].includes(u.protocol)?u.href:'#';}catch{return '#';}}
function choose(name){if(selected)map.setFeatureState({source:'provinces',id:selected},{selected:false});selected=name;map.setFeatureState({source:'provinces',id:name},{selected:true});select.value=name;show(name);}
function clearSelection(){if(selected){map.setFeatureState({source:'provinces',id:selected},{selected:false});selected='';}select.value='';}

map.on('load',()=>{
  map.addSource('provinces',{type:'geojson',data:geo,promoteId:'name'});
  map.addLayer({id:'province-fill',type:'fill',source:'provinces',paint:{'fill-color':['interpolate',['linear'],['get','record_count'],0,'#dce4cf',20,'#c0d2ac',60,'#829e78',120,'#255e4b'],'fill-opacity':['case',['boolean',['feature-state','selected'],false],0.95,0.78]}});
  map.addLayer({id:'province-line',type:'line',source:'provinces',paint:{'line-color':'#f9f8f3','line-width':1.2}});
  map.addLayer({id:'province-selected-line',type:'line',source:'provinces',paint:{'line-color':['case',['boolean',['feature-state','selected'],false],'#d77a4b','#f9f8f3'],'line-width':['case',['boolean',['feature-state','selected'],false],2.5,1.2]}});
  map.on('mousemove','province-fill',e=>{map.getCanvas().style.cursor='pointer';const f=e.features?.[0];if(f){select.value=f.properties.name;show(f.properties.name);}});
  map.on('mouseleave','province-fill',()=>{map.getCanvas().style.cursor='';if(selected){select.value=selected;show(selected);}else{select.value='';document.querySelector('#details').innerHTML='<div class="empty"><span class="compass">✳</span><h2>Start anywhere</h2><p>Move over the map or choose a province to explore its recordings and cultural-region mix.</p><div class="hint">Scroll to zoom · Drag to explore</div></div>';}});
  map.on('click','province-fill',e=>{const f=e.features?.[0];if(f)choose(f.properties.name);});
  document.querySelector('#datasetNote').textContent=`${data.total.toLocaleString()} recordings · ${data.unresolvedCount} location labels unassigned`;
});
select.addEventListener('change',()=>{if(!select.value){clearSelection();return;}choose(select.value);const f=geo.features.find(x=>x.properties.name===select.value);if(f){const b=new maplibregl.LngLatBounds();const visit=c=>Array.isArray(c[0])?c.forEach(visit):b.extend(c);visit(f.geometry.coordinates);map.fitBounds(b,{padding:70,maxZoom:5.5,duration:700});}});
