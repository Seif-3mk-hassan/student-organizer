import {call} from "./bridge.js";
export function initPalette(){
  const el=document.getElementById("palette");
  if(!el) return;
  function open(){ el.hidden=false; el.innerHTML=`<input id=palInput placeholder="Type command or search…"> <div id=palOut></div>`; el.querySelector("#palInput").focus();
    el.querySelector("#palInput").addEventListener("input", async e=>{
      const q=e.target.value.trim();
      if(q.length<2) return;
      try{ const r=await call("search",{q}); document.getElementById("palOut").innerHTML=r.map(x=>`<div>${x.kind}: ${x.snippet}</div>`).join("") }catch{}
    });
  }
  document.addEventListener("keydown", e=>{
    if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==="k"){ e.preventDefault(); open(); }
    if(e.key==="/" && !/input|textarea/i.test(document.activeElement.tagName||"")){ e.preventDefault(); open(); }
    if(e.key==="Escape") el.hidden=true;
  });
}
