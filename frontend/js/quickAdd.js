import {call} from "./bridge.js";
let _qaBound = false;
export function initQuickAdd(){
  const main=document.getElementById("main");
  if(!main || document.getElementById("quickAdd")) return;
  if(_qaBound) return; _qaBound = true;
  const bar=document.createElement("div");
  bar.id="quickAdd"; bar.innerHTML=`<input id=qa placeholder="Add CS101 HW3 due Friday — press Enter"> <small style="color:var(--muted)">Enter to add · N to focus</small>`;
  main.prepend(bar);
  const inp=bar.querySelector("#qa");
  // prevent palette (/) from stealing focus
  inp.addEventListener("keydown", e=> e.stopPropagation());
  document.addEventListener("keydown", e=>{
    if(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA") return;
    if(e.key.toLowerCase()==="n"){ e.preventDefault(); inp.focus(); }
  });
  inp.addEventListener("keydown", async e=>{
    if(e.key==="Enter"){
      const text=inp.value.trim(); if(!text) return;
      try{
        const parsed=await call("quickAdd",{text});
        const title=(parsed.title || text).replace(/\s+in\s+\d+\/\d+\/\d+$/,"").trim() || text;
        const courses=await call("listCourses",{});
        let cid = null;
        if(parsed.course_code) {
          const hit=courses.find(c=>c.code.toLowerCase()===parsed.course_code.toLowerCase());
          if(hit) cid=hit.id;
        }
        if(!cid && courses[0]) cid=courses[0].id;
        if(!cid) throw new Error("Create a course first");
        // handle "in 9/6/2026" explicit date
        let due = parsed.due_date ? new Date(parsed.due_date) : new Date();
        const m=text.match(/in\s+(\d{1,2})\/(\d{1,2})\/(\d{4})/);
        if(m){ due=new Date(parseInt(m[3]), parseInt(m[1])-1, parseInt(m[2]), 23,59,0); }
        await call("createAssignment",{course_id:cid, title, due_date: due.toISOString()});
        inp.value=""; location.reload();
      }catch(err){ alert(err.message); }
    }
  });
}
