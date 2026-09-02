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

async function renderDashboard(){
  const m=document.getElementById("main");
  m.innerHTML = `<h1>Dashboard</h1><div id=qaWrap></div><div id=dash></div>`;
  initQuickAdd();
  try{
    const sems=await call("listSemesters");
    const courses= sems.length ? await call("listCourses",{semester_id:sems[0].id}) : [];
    const assigns = await call("listAssignments");
    const due = assigns.filter(a=> a.status==="todo").slice(0,5);
    const hasData = sems.length>0;
    m.querySelector("#dash").innerHTML = hasData ? `
      <div class=card><b>Due today/tomorrow</b><div>${due.length? due.map(d=>`<div class=row>${d.title} — ${new Date(d.due).toLocaleDateString()} ${d.late?'<span class=banner>late</span>':''}</div>`).join("") : `<div class=empty>All caught up! 🎉</div>`}</div></div>
      <div class=card style=margin-top:12px><b>GPA</b> <span id=gpa>…</span></div>
    ` : `
      <div class=empty><b>No courses yet</b><p>Add your first course or Import ICS</p><button onclick="location.hash='courses'">Add course</button></div>
    `;
    if(hasData){
      try{ const g=await call("getGpa",{}); document.getElementById("gpa").textContent = g.gpa; }catch{}
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
    document.getElementById("list").innerHTML = cs.length? cs.map(c=>`<div class=row><span class=dot style=background:var(--accent)></span> ${c.code} — ${c.name} (${c.credits})</div>`).join("") : `<div class=empty>No courses yet — add one above</div>`;
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
  m.innerHTML = `<h1>Timetable</h1><div id=tt class=card>Loading…</div>`;
  m.querySelector("#tt").innerHTML = `<div class=empty>No classes this term — add a slot from a course. Overlap will be flagged.</div>`;
}

async function render(){
  const h=(location.hash||"#dashboard").slice(1);
  document.querySelectorAll("#sidebar a").forEach(a=> a.classList.toggle("active", a.dataset.r===h));
  (routes[h]||routes.dashboard)();
}

nav(); initPalette(); render(); window.addEventListener("hashchange", render);
