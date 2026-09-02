import {call} from "./bridge.js";
import {initPalette} from "./palette.js";
import {initQuickAdd} from "./quickAdd.js";

const routes = {
  dashboard: renderDashboard,
  courses: renderCourses,
  timetable: renderTimetable,
};

function nav(){
  const s=document.getElementById("sidebar");
  s.innerHTML = `
    <b>Student Organizer</b>
    <a href="#dashboard" data-r=dashboard><span>Dashboard</span></a>
    <a href="#timetable" data-r=timetable><span>Timetable</span></a>
    <a href="#courses" data-r=courses><span>Courses</span></a>
  `;
  s.querySelectorAll("a").forEach(a=> a.addEventListener("click", e=>{
    const r=a.dataset.r; if(r) { location.hash=r; render(); }
  }));
}

function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function pillFor(a){
  const d=new Date(a.due); d.setHours(0,0,0,0);
  const today=new Date(); today.setHours(0,0,0,0);
  const diff=Math.floor((d - today)/86400000);
  if(a.late) return `<span class=badge>late</span>`;
  if(diff===0) return `<span class="badge ok">today</span>`;
  if(diff===1) return `<span class=badge>tomorrow</span>`;
  if(diff>1 && diff<=3) return `<span class=badge muted>in ${diff}d</span>`;
  return `<span class=badge muted>${d.toLocaleDateString()}</span>`;
}
function gpaColor(g){ if(g>=3.5) return "#0e4d45"; if(g>=3) return "#1a7f64"; if(g>=2) return "#c45a2b"; return "#9b1c1c"; }

async function renderDashboard(){
  const m=document.getElementById("main");
  m.innerHTML = `<h1>Dashboard</h1><div id=qaWrap></div><div id=dash></div>`;
  initQuickAdd();
  try{
    const sems=await call("listSemesters");
    const courses= sems.length ? await call("listCourses",{semester_id:sems[0].id}) : [];
    const assigns = await call("listAssignments");
    const todo = assigns.filter(a=> a.status==="todo").sort((x,y)=> new Date(x.due)-new Date(y.due));
    const hasData = sems.length>0;
    const g = hasData ? await call("getGpa",{}).catch(()=>({gpa:0, count:0})) : {gpa:0, count:0};
    const gpa = g.gpa ?? 0;
    m.querySelector("#dash").innerHTML = hasData ? `
      <div class=card>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <b>Due next</b><span class=badge muted>${todo.length} todo</span>
        </div>
        <div>${todo.length? todo.slice(0,8).map(a=>`
          <div class=row>
            <div style="min-width:0;flex:1">
              <div style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(a.title)}</div>
              <div style="font-size:13px;color:var(--muted)">${new Date(a.due).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})} · <a href="#" data-cid="${a.course_id}" style="font-size:12px">view</a></div>
            </div>
            <div style="display:flex;gap:6px;align-items:center">
              ${pillFor(a)}
              <button data-done="${a.id}" title="Mark done" style="border:1px solid var(--border);border-radius:6px;padding:4px 8px;background:#fff;cursor:pointer">✓</button>
              <button data-del="${a.id}" title="Delete" style="border:1px solid #fecaca;border-radius:6px;padding:4px 8px;background:#fff;cursor:pointer">✕</button>
            </div>
          </div>`).join("") : `<div class=empty>All caught up! 🎉 No deadlines — add one above.</div>`}
        </div>
      </div>
      <div class=card>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <b>GPA</b><span style="font-size:22px;font-weight:700;color:${gpaColor(gpa)}">${Number(gpa).toFixed(2)}</span>
        </div>
        <div style="height:8px;background:#eee;border-radius:999px;overflow:hidden;margin-top:10px">
          <div style="width:${Math.min(100, (gpa/4)*100)}%;height:100%;background:${gpaColor(gpa)}"></div>
        </div>
        <div style="font-size:12px;color:var(--muted);margin-top:6px">${g.count? `${g.count} graded items — add more in Courses to update` : "No grades yet — open a course → Grades → Add (e.g. Midterm 85/100 weight 30). 5 courses ≠ GPA until grades exist."} · <a href="#courses">Manage courses</a></div>
        ${gpa>0 && gpa<2 ? `<div class=banner style="margin-top:10px">Heads up: GPA below 2.0 — check absence & upcoming deadlines.</div>` : ""}
      </div>
    ` : `
      <div class=empty><b>No courses yet</b><p>Add your first course or Import ICS</p><button onclick="location.hash='courses'" style="margin-top:8px;padding:8px 12px;border-radius:8px;border:1px solid var(--border)">Add course</button></div>
    `;
    if(hasData){
      m.querySelectorAll("[data-del]").forEach(b=> b.onclick= async ()=>{ await call("deleteAssignment",{id: parseInt(b.dataset.del)}); renderDashboard(); });
      m.querySelectorAll("[data-done]").forEach(b=> b.onclick= async ()=>{ await call("updateAssignment",{id: parseInt(b.dataset.done), status:"done"}); renderDashboard(); });
    }
  }catch(e){
    m.querySelector("#dash").innerHTML = `<div class=banner>DB locked — retry <button onclick="location.reload()">Retry</button></div>`;
  }
}

async function renderCourses(){
  const m=document.getElementById("main");
  m.innerHTML = `<h1>Courses</h1>
    <div class=card><input id=cc placeholder=Code> <input id=cn placeholder=Name> <input id=cr type=number placeholder=Credits> <button id=addC>Add</button></div>
    <div id=list></div>`;
  async function refresh(){
    const sems=await call("listSemesters");
    let sid = sems[0]?.id;
    if(!sid){
      const r=await call("createSemester",{name:"Fall 2026", start_date:"2026-09-01", end_date:"2026-12-20"});
      sid=r.id;
    }
    const cs=await call("listCourses",{semester_id:sid});
    document.getElementById("list").innerHTML = cs.length? cs.map(c=>`
      <div class=row style="flex-wrap:wrap;gap:8px">
        <span class=dot style=background:var(--accent)></span> <b>${esc(c.code)}</b> — ${esc(c.name)} (${c.credits} cr)
        <span style="flex:1"></span>
        <input id="g-${c.id}-name" placeholder="Item e.g. Midterm" style="width:130px;padding:6px;border:1px solid var(--border);border-radius:6px">
        <input id="g-${c.id}-score" type=number placeholder="85" style="width:60px;padding:6px;border:1px solid var(--border);border-radius:6px">
        <span>/</span><input id="g-${c.id}-max" type=number placeholder="100" style="width:60px;padding:6px;border:1px solid var(--border);border-radius:6px">
        <input id="g-${c.id}-w" type=number placeholder="wt 30" style="width:60px;padding:6px;border:1px solid var(--border);border-radius:6px">
        <button data-addg="${c.id}" style="padding:6px 10px;border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:6px;cursor:pointer">Add grade</button>
        <button data-delc="${c.id}" style="padding:6px 10px;border:1px solid #fecaca;background:#fff;border-radius:6px;cursor:pointer">Delete course</button>
        <button data-gpa="${c.id}" style="padding:6px 10px;border:1px solid var(--border);background:#fff;border-radius:6px;cursor:pointer">GPA</button>
        <span id="gpa-${c.id}" style="font-size:12px;color:var(--muted)"></span>
      </div>`).join("") : `<div class=empty>No courses yet — add one above</div>`;
    document.querySelectorAll("[data-addg]").forEach(b=> b.onclick = async ()=>{
      const id=b.dataset.addg;
      const item=document.getElementById(`g-${id}-name`).value.trim(), score=parseFloat(document.getElementById(`g-${id}-score`).value), max=parseFloat(document.getElementById(`g-${id}-max`).value), w=parseFloat(document.getElementById(`g-${id}-w`).value);
      if(!item||isNaN(score)||isNaN(max)||isNaN(w)) return alert("Fill item, score, max, weight");
      try{ await call("addGrade",{course_id:parseInt(id), item_name:item, score, max_score:max, weight:w}); alert("Grade added — dashboard GPA will update"); }catch(e){ alert(e.message); }
    });
    document.querySelectorAll("[data-delc]").forEach(b=> b.onclick = async ()=>{ if(!confirm("Delete course and its assignments/grades?")) return; await call("deleteCourse",{id: parseInt(b.dataset.delc)}); refresh(); });
    document.querySelectorAll("[data-gpa]").forEach(b=> b.onclick = async ()=>{
      const r=await call("getGpa",{course_id: parseInt(b.dataset.gpa)});
      document.getElementById(`gpa-${b.dataset.gpa}`).textContent = ` GPA ${Number(r.gpa).toFixed(2)} (${r.count})`;
    });
    document.getElementById("addC").onclick = async ()=>{
      const code=document.getElementById("cc").value.trim(), name=document.getElementById("cn").value.trim(), credits=parseInt(document.getElementById("cr").value||"3");
      if(!code||!name) return alert("code + name required");
      try{ await call("createCourse",{semester_id:sid, code, name, credits}); refresh(); }catch(e){ alert(e.message); }
    };
  }
  refresh();
}

async function renderTimetable(){
  const m=document.getElementById("main");
  m.innerHTML = `<h1>Timetable</h1>
    <div class=card>
      <b>Add slot</b>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
        <select id=tsCourse style="padding:6px;border:1px solid var(--border);border-radius:6px"></select>
        <select id=tsDay style="padding:6px;border:1px solid var(--border);border-radius:6px">
          <option value=0>Mon</option><option value=1>Tue</option><option value=2>Wed</option><option value=3>Thu</option><option value=4>Fri</option><option value=5>Sat</option><option value=6>Sun</option>
        </select>
        <input id=tsStart type=time value="09:00" style="padding:6px;border:1px solid var(--border);border-radius:6px">
        <input id=tsEnd type=time value="10:30" style="padding:6px;border:1px solid var(--border);border-radius:6px">
        <input id=tsRoom placeholder=Room style="width:80px;padding:6px;border:1px solid var(--border);border-radius:6px">
        <button id=tsAdd style="padding:6px 12px;background:var(--accent);color:#fff;border:1px solid var(--accent);border-radius:6px;cursor:pointer">Add</button>
      </div>
      <div id=tsMsg style="font-size:12px;color:#9b1c1c;margin-top:6px"></div>
    </div>
    <div id=tt style="margin-top:14px"></div>`;
  const days=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  const courses=await call("listCourses",{}).catch(()=>[]);
  const sel=m.querySelector("#tsCourse");
  sel.innerHTML = courses.map(c=>`<option value=${c.id}>${esc(c.code)} — ${esc(c.name)}</option>`).join("") || `<option value="">No courses — add one</option>`;
  async function refresh(){
    const slots=await call("listSlots",{}).catch(()=>[]);
    if(!slots.length){ m.querySelector("#tt").innerHTML = `<div class=empty>No classes this term — add a slot above. Overlap will be flagged.</div>`; return; }
    let html = `<div style="display:grid;grid-template-columns:80px repeat(7,1fr);gap:6px;font-size:13px">`;
    html+=`<div></div>`+days.map(d=>`<b style="text-align:center">${d}</b>`).join("");
    // time slots 08-20
    for(let h=8;h<20;h++){
      html+=`<div style="color:var(--muted);padding:6px 0">${String(h).padStart(2,'0')}:00</div>`;
      for(let d=0;d<7;d++){
        const cell = slots.filter(s=> s.day===d && parseInt(s.start.split(":")[0])===h);
        html+=`<div style="min-height:36px;border:1px solid #eee;border-radius:6px;background:#fff;padding:4px">${
          cell.map(s=>`<div style="background:var(--surface);border-left:3px solid var(--accent);padding:4px 6px;border-radius:6px;font-size:12px;margin-bottom:4px">${esc(s.code)} ${esc(s.start)}-${esc(s.end)} <a href="#" data-delSlot="${s.id}" style="color:#9b1c1c">✕</a></div>`).join("")
        }</div>`;
      }
    }
    html+=`</div>`;
    m.querySelector("#tt").innerHTML=html;
    m.querySelectorAll("[data-delSlot]").forEach(b=> b.onclick= async (e)=>{ e.preventDefault(); await call("deleteSlot",{id:parseInt(b.dataset.delSlot)}); refresh(); });
  }
  m.querySelector("#tsAdd").onclick = async ()=>{
    const course_id=parseInt(sel.value), day_of_week=parseInt(m.querySelector("#tsDay").value), start_time=m.querySelector("#tsStart").value, end_time=m.querySelector("#tsEnd").value, room=m.querySelector("#tsRoom").value;
    if(!course_id) return m.querySelector("#tsMsg").textContent="Pick a course first";
    const r=await call("createSlot",{course_id, day_of_week, start_time, end_time, room});
    if(!r || r.id===undefined && !r.ok){ /* bridge returns {ok,id} or {ok:false} */ }
    // call returns {ok,id} on success, but our wrapper throws; handle both
    refresh();
  };
  // monkey-patch createSlot error display: wrap call
  const origCreate = window.pywebview?.api?.createSlot;
  // instead, override button to catch _err
  m.querySelector("#tsAdd").addEventListener("click", async ()=>{
    try{ }catch(e){ m.querySelector("#tsMsg").textContent=e.message; }
  });
  await refresh();
  // attach proper error handler by replacing click
  m.querySelector("#tsAdd").onclick = async ()=>{
    m.querySelector("#tsMsg").textContent="";
    const course_id=parseInt(sel.value), day_of_week=parseInt(m.querySelector("#tsDay").value), start_time=m.querySelector("#tsStart").value+":00", end_time=m.querySelector("#tsEnd").value+":00", room=m.querySelector("#tsRoom").value;
    if(!course_id) return m.querySelector("#tsMsg").textContent="Pick a course";
    try{ await call("createSlot",{course_id, day_of_week, start_time, end_time, room}); await refresh(); }catch(e){ m.querySelector("#tsMsg").textContent=e.message; }
  };
}

async function render(){
  const h=(location.hash||"#dashboard").slice(1);
  document.querySelectorAll("#sidebar a").forEach(a=> a.classList.toggle("active", a.dataset.r===h));
  (routes[h]||routes.dashboard)();
}

nav(); initPalette(); render(); window.addEventListener("hashchange", render);
