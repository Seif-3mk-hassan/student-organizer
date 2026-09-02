import {call} from "./bridge.js";
export function initQuickAdd(){
  const main=document.getElementById("main");
  if(!main || document.getElementById("quickAdd")) return;
  const bar=document.createElement("div");
  bar.id="quickAdd"; bar.innerHTML=`<input id=qa placeholder="Add CS101 HW3 due Friday — press Enter"> <small>Enter to add · N to focus</small>`;
  main.prepend(bar);
  const inp=bar.querySelector("#qa");
  document.addEventListener("keydown", e=>{ if(e.key.toLowerCase()==="n" && !/input|textarea/i.test(document.activeElement.tagName||"")){ inp.focus(); }});
  inp.addEventListener("keydown", async e=>{
    if(e.key==="Enter"){
      const text=inp.value.trim(); if(!text) return;
      try{
        const parsed=await call("quickAdd",{text});
        const title=parsed.title || text;
        // naive: create assignment in first course of parsed code or first course
        const courses=await call("listCourses",{});
        let cid = null;
        if(parsed.course_code) {
          const hit=courses.find(c=>c.code===parsed.course_code);
          if(hit) cid=hit.id;
        }
        if(!cid && courses[0]) cid=courses[0].id;
        if(!cid) throw new Error("Create a course first");
        await call("createAssignment",{course_id:cid, title, due_date:(parsed.due_date|| new Date()).toISOString()});
        inp.value=""; location.reload();
      }catch(err){ alert(err.message); }
    }
  });
}
