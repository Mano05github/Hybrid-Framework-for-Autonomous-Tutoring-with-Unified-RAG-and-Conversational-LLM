
content = """\
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Vaathiyar — AI-Powered Learning Platform</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="{% static 'css/landing.css' %}" />
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
<style>
/* ====================================================================
   VAATHIYAR — CINEMATIC LANDING (inline)
   ==================================================================== */
body { background: #080b14; }

/* canvas */
#vx-canvas {
  position: fixed; inset: 0; z-index: 0;
  pointer-events: none; opacity: 0.38;
}

/* ── Nav ──────────────────────────────────────────────────────────── */
.vx-nav {
  position: fixed; top: 0; left: 0; right: 0; height: 72px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 3.5rem; z-index: 500;
  transition: background 0.4s, border-color 0.4s;
}
.vx-nav.solid {
  background: rgba(8,11,20,0.93);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.vx-brand {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.05rem; font-weight: 800; letter-spacing: 0.08em;
  color: #f1f5f9; text-decoration: none;
  display: flex; align-items: center; gap: 10px;
}
.vx-brand-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  background: #63b3ed; box-shadow: 0 0 10px #63b3ed;
  animation: vxPulse 2.2s ease-in-out infinite; flex-shrink: 0;
}
@keyframes vxPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.6)} }
.vx-nav-links { display: flex; gap: 1.75rem; align-items: center; }
.vx-nav-a { font-size: .875rem; color: #64748b; text-decoration: none; transition: color .2s; font-weight: 500; }
.vx-nav-a:hover { color: #f1f5f9; }
.vx-nav-btn {
  background: #63b3ed; color: #080b14;
  padding: .5rem 1.2rem; border-radius: 8px;
  font-size: .875rem; font-weight: 700; text-decoration: none;
  transition: background .2s, box-shadow .2s, transform .15s;
}
.vx-nav-btn:hover { background: #90cdf4; box-shadow: 0 4px 22px rgba(99,179,237,.45); transform: translateY(-1px); }

/* ── Hero ─────────────────────────────────────────────────────────── */
.vx-hero {
  position: relative; z-index: 1;
  min-height: 100vh;
  display: grid; grid-template-columns: 1fr 1fr;
  align-items: center; gap: 3.5rem;
  padding: 9rem 5rem 5rem;
  max-width: 1380px; margin: 0 auto;
}
.vx-eyebrow {
  display: inline-flex; align-items: center; gap: .5rem;
  background: rgba(99,179,237,.07); border: 1px solid rgba(99,179,237,.22);
  border-radius: 99px; padding: .38rem 1rem;
  font-size: .75rem; font-weight: 600; color: #63b3ed;
  letter-spacing: .07em; text-transform: uppercase; margin-bottom: 1.75rem;
}
.vx-hero-h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(3rem,4.8vw,5.2rem); font-weight: 800;
  line-height: 1.0; letter-spacing: -.03em; color: #f1f5f9; margin-bottom: 1.5rem;
}
.vx-grad-text {
  background: linear-gradient(95deg,#63b3ed 0%,#a78bfa 40%,#f472b6 70%,#63b3ed 100%);
  background-size: 300% 100%;
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradFlow 5s ease infinite;
}
@keyframes gradFlow { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.vx-hero-sub { font-size: 1.1rem; color: #94a3b8; line-height: 1.75; max-width: 500px; margin-bottom: 2.5rem; }
.vx-hero-ctas { display: flex; gap: .9rem; flex-wrap: wrap; }
.vx-btn-primary {
  background: #63b3ed; color: #080b14;
  padding: .8rem 1.9rem; border-radius: 10px;
  font-size: .96rem; font-weight: 700; text-decoration: none;
  transition: background .2s, box-shadow .2s, transform .15s;
  display: inline-flex; align-items: center; gap: .5rem;
}
.vx-btn-primary:hover { background: #90cdf4; box-shadow: 0 6px 28px rgba(99,179,237,.4); transform: translateY(-2px); }
.vx-btn-ghost {
  background: transparent; color: #f1f5f9;
  border: 1px solid rgba(255,255,255,.14); border-radius: 10px;
  padding: .8rem 1.9rem; font-size: .96rem; font-weight: 500; text-decoration: none;
  transition: border-color .2s, color .2s, background .2s;
  display: inline-flex; align-items: center; gap: .5rem;
}
.vx-btn-ghost:hover { border-color: rgba(99,179,237,.4); color: #63b3ed; background: rgba(99,179,237,.06); }
.vx-hero-stats {
  display: flex; gap: 2.5rem; margin-top: 3rem;
  padding-top: 2.5rem; border-top: 1px solid rgba(255,255,255,.07);
}
.vx-stat-val { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; color: #f1f5f9; display: block; line-height: 1; }
.vx-stat-lbl { font-size: .72rem; color: #475569; text-transform: uppercase; letter-spacing: .07em; margin-top: .3rem; display: block; }

/* ── Terminal ─────────────────────────────────────────────────────── */
.vx-terminal {
  background: #0d1117;
  border: 1px solid rgba(255,255,255,.1); border-radius: 18px; overflow: hidden;
  box-shadow: 0 48px 120px rgba(0,0,0,.75), 0 0 0 1px rgba(255,255,255,.04), inset 0 1px 0 rgba(255,255,255,.06);
  transform: perspective(1200px) rotateY(-5deg) rotateX(2deg);
  transition: transform .5s cubic-bezier(.25,.46,.45,.94);
}
.vx-terminal:hover { transform: perspective(1200px) rotateY(0deg) rotateX(0deg); }
.vx-term-bar {
  background: #161b22; padding: 13px 16px;
  display: flex; align-items: center; gap: 7px;
  border-bottom: 1px solid rgba(255,255,255,.07);
}
.tdot { width: 12px; height: 12px; border-radius: 50%; }
.td-r{background:#ff5f57} .td-y{background:#ffbd2e} .td-g{background:#27c93f}
.vx-term-label { font-size: .74rem; color: #475569; font-family: monospace; margin-left: auto; }
.vx-term-body { padding: 1.25rem 1.25rem 1rem; min-height: 340px; }
.vx-msg { margin-bottom: .9rem; animation: msgIn .4s ease forwards; }
@keyframes msgIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.vx-msg-who { font-size: .66rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .3rem; }
.vx-msg-who.ai{color:#63b3ed} .vx-msg-who.usr{color:#475569}
.vx-bubble { display: inline-block; max-width: 88%; padding: .6rem .9rem; border-radius: 12px; font-size: .84rem; line-height: 1.55; }
.vx-bubble.ai  { background: rgba(99,179,237,.1); color: #e2e8f0; border-radius: 12px 12px 12px 3px; }
.vx-bubble.usr { background: rgba(255,255,255,.05); color: #94a3b8; border-radius: 12px 12px 3px 12px; }
.vx-typing-row { padding: .5rem 0; }
.vx-dots { display: inline-flex; gap: 5px; align-items: center; padding: .55rem .8rem; background: rgba(99,179,237,.08); border-radius: 12px 12px 12px 3px; }
.vx-dots span { width:6px;height:6px;border-radius:50%;background:#63b3ed;animation:dotB 1.2s ease-in-out infinite;}
.vx-dots span:nth-child(2){animation-delay:.2s} .vx-dots span:nth-child(3){animation-delay:.4s}
@keyframes dotB { 0%,80%,100%{opacity:.2;transform:scale(.7)} 40%{opacity:1;transform:scale(1)} }

/* ── Section scaffolding ──────────────────────────────────────────── */
.vx-section  { position: relative; z-index: 1; padding: 7rem 5rem; max-width: 1380px; margin: 0 auto; }
.vx-full-row { position: relative; z-index: 1; width: 100%; }
.vx-alt-bg   { background: rgba(10,13,22,.97); }
.vx-sec-label {
  font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: .12em;
  color: #8b5cf6; margin-bottom: .75rem;
  display: flex; align-items: center; gap: .6rem;
}
.vx-sec-label::before { content:""; width:20px; height:1px; background:#8b5cf6; }
.vx-sec-h2 { font-family: 'Space Grotesk', sans-serif; font-size: clamp(1.9rem,3vw,2.9rem); font-weight: 700; color: #f1f5f9; letter-spacing: -.02em; margin-bottom: .75rem; }
.vx-sec-p  { font-size: .96rem; color: #64748b; max-width: 480px; line-height: 1.7; }
.vx-sec-divider { height: 1px; background: linear-gradient(90deg,transparent,rgba(255,255,255,.06),transparent); margin: 0 5rem; position: relative; z-index: 1; }

/* ── How it works ─────────────────────────────────────────────────── */
.vx-steps { display: grid; grid-template-columns: repeat(3,1fr); gap: 2rem; margin-top: 3.5rem; position: relative; }
.vx-steps::before {
  content:""; position: absolute; top: 39px; left: 17%; right: 17%; height: 1px;
  background: linear-gradient(90deg,rgba(99,179,237,.25),rgba(139,92,246,.25),rgba(99,179,237,.25));
}
.vx-step { text-align: center; padding: 0 1.5rem; }
.vx-step-ring {
  width: 80px; height: 80px; border-radius: 50%;
  background: #0d1117; border: 1px solid rgba(255,255,255,.09);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 1.4rem; position: relative; z-index: 1;
  transition: border-color .3s, box-shadow .3s;
}
.vx-step:hover .vx-step-ring { border-color: rgba(99,179,237,.4); box-shadow: 0 0 28px rgba(99,179,237,.15); }
.vx-step-badge {
  position: absolute; top: -3px; right: -3px;
  width: 22px; height: 22px; border-radius: 50%;
  background: #63b3ed; color: #080b14;
  font-size: .62rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.vx-step-title { font-family: 'Space Grotesk', sans-serif; font-size: .98rem; font-weight: 600; color: #f1f5f9; margin-bottom: .5rem; }
.vx-step-desc  { font-size: .83rem; color: #64748b; line-height: 1.65; }

/* ── Agent cards ──────────────────────────────────────────────────── */
.vx-agents { display: grid; grid-template-columns: repeat(2,1fr); gap: 1.25rem; margin-top: 3rem; }
.vx-agent {
  background: #0a0d16; border: 1px solid rgba(255,255,255,.07); border-radius: 20px;
  padding: 1.75rem; position: relative; overflow: hidden;
  transition: transform .3s cubic-bezier(.25,.46,.45,.94), border-color .3s;
}
.vx-agent::after {
  content:""; position: absolute; inset: 0; opacity: 0;
  background: radial-gradient(ellipse at 20% 20%, var(--ac-a), transparent 65%);
  transition: opacity .45s;
}
.vx-agent:hover { transform: translateY(-5px); border-color: var(--ac-b); }
.vx-agent:hover::after { opacity: 1; }
.vx-agent-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.2rem; position: relative; z-index: 1; }
.vx-agent-icon { width: 52px; height: 52px; border-radius: 14px; background: var(--ac-bg); border: 1px solid var(--ac-b); display: flex; align-items: center; justify-content: center; }
.vx-agent-badge { font-size: .66rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ac-c); background: var(--ac-bg); border: 1px solid var(--ac-b); padding: .3rem .7rem; border-radius: 6px; }
.vx-agent-name { font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: .5rem; position: relative; z-index: 1; }
.vx-agent-desc { font-size: .86rem; color: #64748b; line-height: 1.65; position: relative; z-index: 1; }
.vx-agent-tags { display: flex; gap: .45rem; margin-top: 1.2rem; flex-wrap: wrap; position: relative; z-index: 1; }
.vx-agent-tag { font-size: .7rem; padding: .25rem .6rem; border-radius: 6px; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.07); color: #94a3b8; }

/* ── Bento grid ───────────────────────────────────────────────────── */
.vx-bento { display: grid; grid-template-columns: repeat(3,1fr); gap: 1.25rem; margin-top: 3rem; }
.vx-bc {
  background: #0a0d16; border: 1px solid rgba(255,255,255,.07); border-radius: 18px;
  padding: 1.75rem; position: relative; overflow: hidden;
  transition: border-color .25s, transform .2s;
}
.vx-bc:hover { border-color: rgba(255,255,255,.13); transform: translateY(-3px); }
.vx-bc.span2 { grid-column: span 2; }
.vx-bc-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 1.2rem; }
.vx-bc-lbl   { font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; margin-bottom: .4rem; }
.vx-bc-big   { font-family: 'Space Grotesk', sans-serif; font-size: 2.8rem; font-weight: 800; color: #f1f5f9; letter-spacing: -.04em; line-height: 1; margin-bottom: .25rem; }
.vx-bc-title { font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 700; color: #f1f5f9; margin-bottom: .4rem; }
.vx-bc-desc  { font-size: .82rem; color: #64748b; line-height: 1.65; }
.vx-bc-bar   { height: 4px; border-radius: 2px; margin-top: 1rem; }

/* ── CTA ──────────────────────────────────────────────────────────── */
.vx-cta-wrap { position: relative; z-index: 1; padding: 5rem 5rem 7rem; }
.vx-cta-box {
  max-width: 820px; margin: 0 auto; text-align: center;
  background: linear-gradient(140deg,rgba(99,179,237,.05),rgba(139,92,246,.05));
  border: 1px solid rgba(99,179,237,.18); border-radius: 28px;
  padding: 4rem; position: relative; overflow: hidden;
}
.vx-cta-box::before {
  content:""; position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 55%; height: 1px;
  background: linear-gradient(90deg,transparent,rgba(99,179,237,.6),transparent);
}
.vx-cta-h { font-family: 'Space Grotesk', sans-serif; font-size: clamp(1.9rem,3.5vw,2.8rem); font-weight: 800; color: #f1f5f9; letter-spacing: -.02em; margin-bottom: 1rem; }
.vx-cta-p { font-size: 1rem; color: #94a3b8; margin-bottom: 2rem; line-height: 1.65; max-width: 500px; margin-left: auto; margin-right: auto; }
.vx-cta-btns { display: flex; gap: .9rem; justify-content: center; flex-wrap: wrap; position: relative; z-index: 1; }

/* ── Footer ───────────────────────────────────────────────────────── */
.vx-footer {
  position: relative; z-index: 1;
  background: #050810; border-top: 1px solid rgba(255,255,255,.05);
  padding: 2.5rem 5rem;
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
}
.vx-footer-brand { font-family: 'Space Grotesk', sans-serif; font-size: .9rem; font-weight: 800; letter-spacing: .07em; color: #f1f5f9; }
.vx-footer-sub   { font-size: .73rem; color: #1e293b; margin-top: .2rem; }
.vx-footer-copy  { font-size: .75rem; color: #1e293b; }

/* ── Responsive ───────────────────────────────────────────────────── */
@media(max-width:1100px){
  .vx-hero { grid-template-columns: 1fr; padding: 9rem 3rem 4rem; max-width: 700px; }
  .vx-terminal { transform: none; max-width: 540px; }
  .vx-agents { grid-template-columns: 1fr; }
}
@media(max-width:768px){
  .vx-nav { padding: 0 1.5rem; }
  .vx-nav .vx-nav-a { display: none; }
  .vx-hero { padding: 7.5rem 1.5rem 3rem; }
  .vx-section { padding: 5rem 1.5rem; }
  .vx-steps { grid-template-columns: 1fr; gap: 2rem; }
  .vx-steps::before { display: none; }
  .vx-agents { grid-template-columns: 1fr; }
  .vx-bento { grid-template-columns: 1fr; }
  .vx-bc.span2 { grid-column: span 1; }
  .vx-cta-wrap { padding: 3rem 1.5rem 5rem; }
  .vx-cta-box { padding: 2.5rem 1.5rem; }
  .vx-footer { padding: 2rem 1.5rem; flex-direction: column; }
  .vx-sec-divider { margin: 0 1.5rem; }
}
</style>
</head>
<body>
<div class="noise-overlay"></div>
<canvas id="vx-canvas"></canvas>
<div id="root"></div>

<!-- Neural particle network -->
<script>
(function(){
  var c=document.getElementById("vx-canvas"),ctx=c.getContext("2d"),W,H,pts;
  var N=75,D=155;
  function rsz(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;}
  function mkPt(){return{x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,r:Math.random()*1.4+.4};}
  function init(){rsz();pts=[];for(var i=0;i<N;i++)pts.push(mkPt());}
  function tick(){
    ctx.clearRect(0,0,W,H);
    for(var i=0;i<N;i++){
      var p=pts[i];
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=W;if(p.x>W)p.x=0;if(p.y<0)p.y=H;if(p.y>H)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle="rgba(99,179,237,.75)";ctx.fill();
      for(var j=i+1;j<N;j++){
        var q=pts[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.sqrt(dx*dx+dy*dy);
        if(d<D){var a=(1-d/D)*.28;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.strokeStyle="rgba(99,179,237,"+a+")";ctx.lineWidth=.6;ctx.stroke();}
      }
    }
    requestAnimationFrame(tick);
  }
  window.addEventListener("resize",rsz);
  init();tick();
})();
</script>

{% verbatim %}
<script type="text/babel">
const { useState, useEffect, useRef } = React;
gsap.registerPlugin(ScrollTrigger);

/* ── data ─────────────────────────────────────────────────────────── */
const AGENTS = [
  { icon:"brain",       role:"Orchestrator", name:"The Supervisor",
    c:"#63b3ed", ca:"rgba(99,179,237,.08)",  cb:"rgba(99,179,237,.22)", cg:"rgba(99,179,237,.12)",
    desc:"The central nervous system of every session. Coordinates all specialists, manages context state, and synthesises multi-agent responses in real time.",
    tags:["Session Control","Agent Routing","State Synthesis"] },
  { icon:"help-circle", role:"Examiner",     name:"Socratic Mind",
    c:"#8b5cf6", ca:"rgba(139,92,246,.08)", cb:"rgba(139,92,246,.22)", cg:"rgba(139,92,246,.12)",
    desc:"Never tells you the answer. Probes your mental model with targeted questions, surfaces hidden gaps, and forces genuine thinking — creating mastery that sticks.",
    tags:["Socratic Questioning","Gap Detection","Concept Depth"] },
  { icon:"mic",         role:"Voice Engine", name:"Speech Core",
    c:"#10b981", ca:"rgba(16,185,129,.08)", cb:"rgba(16,185,129,.22)", cg:"rgba(16,185,129,.12)",
    desc:"Full STT/TTS pipeline with prosody modulation. Speak naturally — the tutor understands context and responds with nuanced voice. Sessions feel like real dialogue.",
    tags:["Speech-to-Text","Text-to-Speech","Prosody Control"] },
  { icon:"code-2",      role:"Code Sandbox", name:"Exec Engine",
    c:"#f59e0b", ca:"rgba(245,158,11,.08)", cb:"rgba(245,158,11,.22)", cg:"rgba(245,158,11,.12)",
    desc:"Executes student code live, analyses runtime faults at line level, and pairs every bug explanation with a Socratic follow-up — turning errors into learning moments.",
    tags:["Live Execution","Error Analysis","Guided Debugging"] }
];

const STEPS = [
  { icon:"user-circle", title:"You open a session",    desc:"Choose a topic or just ask freely. The system infers your current mastery from the first few exchanges — no quiz required." },
  { icon:"cpu",         title:"Agents assemble",       desc:"The Supervisor orchestrates the team. Specialist agents — examiner, voice, analyst, sandbox — activate in milliseconds." },
  { icon:"target",      title:"You reach mastery",     desc:"Socratic dialogue, adaptive depth, and spaced follow-ups build understanding far beneath the surface. Not right answers — deep knowledge." }
];

const BENTO = [
  { icon:"database", c:"#63b3ed", bg:"rgba(99,179,237,.1)",  lbl:"Architecture", title:"Zero-hallucination grounding",  desc:"Responses are anchored to your course materials via semantic vector search and a dedicated knowledge graph. No invented facts.",           span2:true },
  { icon:"zap",      c:"#f59e0b", bg:"rgba(245,158,11,.1)",  lbl:"Latency",      big:"<500ms", title:"Median response time",        desc:"Across all active agents, measured end-to-end in production." },
  { icon:"activity", c:"#10b981", bg:"rgba(16,185,129,.1)",  lbl:"Adaptivity",   title:"Live knowledge model",           desc:"Your mastery state re-computes after every exchange, reshaping question depth and curriculum order automatically." },
  { icon:"repeat",   c:"#8b5cf6", bg:"rgba(139,92,246,.1)",  lbl:"Retention",    title:"Spaced-repetition engine",       desc:"Concepts you struggle with resurface at scientifically optimal intervals, preventing the forgetting curve." },
  { icon:"layers",   c:"#f472b6", bg:"rgba(244,114,182,.1)", lbl:"Multi-modal",  title:"Voice + Text + Code",            desc:"Switch input modes freely mid-session. Speak, type, or paste code — the system follows how you think." }
];

const CONV = [
  { r:"usr", t:"I don't get recursion at all. Can you help?" },
  { r:"ai",  t:"Of course — but first, have you ever opened a Russian nesting doll?" },
  { r:"usr", t:"Yeah, it's a doll inside a doll inside a doll..." },
  { r:"ai",  t:"Exactly. Recursion is a function that calls itself the same way. What do you think happens if there's no smallest doll to stop the opening?" },
  { r:"usr", t:"It would just... never stop?" },
  { r:"ai",  t:"Right — that's a stack overflow. The stopping condition is called the 'base case'. Can you now write a function that counts down from n to 0?" }
];

/* ── Nav ──────────────────────────────────────────────────────────── */
function Nav() {
  const [solid, setSolid] = useState(false);
  useEffect(() => {
    const fn = () => setSolid(window.scrollY > 50);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);
  return (
    <nav className={"vx-nav" + (solid ? " solid" : "")}>
      <a href="#hero" className="vx-brand">
        <div className="vx-brand-pulse"/>VAATHIYAR
      </a>
      <div className="vx-nav-links">
        <a href="#how"      className="vx-nav-a">How it works</a>
        <a href="#agents"   className="vx-nav-a">Agents</a>
        <a href="#features" className="vx-nav-a">Features</a>
        <a href="login.html"    className="vx-nav-a" style={{marginLeft:"0.4rem"}}>Sign In</a>
        <a href="register.html" className="vx-nav-btn">Get Started →</a>
      </div>
    </nav>
  );
}

/* ── Chat terminal ────────────────────────────────────────────────── */
function TerminalCard() {
  const [shown, setShown] = useState(1);
  const [typing, setTyping] = useState(false);
  useEffect(() => {
    function showNext(i) {
      if (i >= CONV.length) return;
      setTyping(true);
      const delay = CONV[i].r === "ai" ? 1400 : 600;
      setTimeout(() => {
        setTyping(false);
        setShown(i + 1);
        const gap = CONV[i].r === "usr" ? 700 : 900;
        setTimeout(() => showNext(i + 1), gap);
      }, delay);
    }
    const t = setTimeout(() => showNext(1), 900);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="vx-terminal">
      <div className="vx-term-bar">
        <div className="tdot td-r"/><div className="tdot td-y"/><div className="tdot td-g"/>
        <span className="vx-term-label">vaathiyar · live session · recursion</span>
      </div>
      <div className="vx-term-body">
        {CONV.slice(0, shown).map((m, i) => (
          <div key={i} className="vx-msg">
            <div className={"vx-msg-who " + m.r}>{m.r === "ai" ? "VAATHIYAR" : "YOU"}</div>
            <div className={"vx-bubble " + m.r}>{m.t}</div>
          </div>
        ))}
        {typing && (
          <div className="vx-typing-row">
            <div className="vx-dots"><span/><span/><span/></div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Hero ─────────────────────────────────────────────────────────── */
function Hero() {
  useEffect(() => {
    gsap.fromTo(".vx-hs > *",
      { opacity:0, y:28 },
      { opacity:1, y:0, duration:.65, stagger:.13, ease:"power3.out", delay:.15 });
    gsap.fromTo(".vx-terminal",
      { opacity:0, x:45 },
      { opacity:1, x:0, duration:.85, ease:"power3.out", delay:.35 });
  }, []);
  return (
    <section className="vx-hero" id="hero">
      <div className="vx-hs">
        <div className="vx-eyebrow">
          <i data-lucide="sparkles" style={{width:13,height:13}}/>
          Multi-Agent · RAG-Grounded · Voice-Native
        </div>
        <h1 className="vx-hero-h1">
          The AI tutor<br/>that <span className="vx-grad-text">thinks with you</span>
        </h1>
        <p className="vx-hero-sub">
          Vaathiyar is a pedagogically-engineered multi-agent system — not a chatbot.
          It adapts to your knowledge state in real time through voice, code, and Socratic dialogue.
        </p>
        <div className="vx-hero-ctas">
          <a href="register.html" className="vx-btn-primary">
            Start Learning Free
            <i data-lucide="arrow-right" style={{width:16,height:16}}/>
          </a>
          <a href="#how" className="vx-btn-ghost">
            <i data-lucide="play-circle" style={{width:16,height:16}}/>
            See how it works
          </a>
        </div>
        <div className="vx-hero-stats">
          {[["8+","AI Agents"],["RAG","Grounded"],["Real-time","Adaptive"],["Voice","Native"]].map(([v,l],i) => (
            <div key={i}><span className="vx-stat-val">{v}</span><span className="vx-stat-lbl">{l}</span></div>
          ))}
        </div>
      </div>
      <TerminalCard/>
    </section>
  );
}

/* ── How it works ─────────────────────────────────────────────────── */
function HowSection() {
  const ref = useRef(null);
  useEffect(() => {
    gsap.fromTo(".vx-step",
      { opacity:0, y:45 },
      { opacity:1, y:0, duration:.6, stagger:.18, ease:"power3.out",
        scrollTrigger:{ trigger:ref.current, start:"top 78%", once:true } });
  }, []);
  return (
    <div className="vx-full-row vx-alt-bg" id="how">
      <div className="vx-section" ref={ref}>
        <div className="vx-sec-label">Process</div>
        <h2 className="vx-sec-h2">How a session unfolds</h2>
        <p className="vx-sec-p">From first question to deep understanding — structured, adaptive, and relentlessly focused on mastery.</p>
        <div className="vx-steps">
          {STEPS.map((s,i) => (
            <div key={i} className="vx-step">
              <div className="vx-step-ring">
                <i data-lucide={s.icon} style={{width:28,height:28,color:"#63b3ed"}}/>
                <div className="vx-step-badge">{i+1}</div>
              </div>
              <div className="vx-step-title">{s.title}</div>
              <p className="vx-step-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Agents ───────────────────────────────────────────────────────── */
function AgentsSection() {
  const ref = useRef(null);
  useEffect(() => {
    gsap.fromTo(".vx-agent",
      { opacity:0, y:55 },
      { opacity:1, y:0, duration:.65, stagger:.16, ease:"power3.out",
        scrollTrigger:{ trigger:ref.current, start:"top 78%", once:true } });
  }, []);
  return (
    <div className="vx-full-row" id="agents">
      <div className="vx-section" ref={ref}>
        <div className="vx-sec-label">Architecture</div>
        <h2 className="vx-sec-h2">Meet your AI team</h2>
        <p className="vx-sec-p">Each agent is a specialist. Together they compose a tutoring experience no single model could deliver.</p>
        <div className="vx-agents">
          {AGENTS.map((a,i) => (
            <div key={i} className="vx-agent"
              style={{"--ac-c":a.c,"--ac-a":a.ca,"--ac-b":a.cb,"--ac-bg":a.cg}}>
              <div className="vx-agent-top">
                <div className="vx-agent-icon">
                  <i data-lucide={a.icon} style={{width:24,height:24,color:a.c}}/>
                </div>
                <div className="vx-agent-badge">{a.role}</div>
              </div>
              <div className="vx-agent-name">{a.name}</div>
              <p className="vx-agent-desc">{a.desc}</p>
              <div className="vx-agent-tags">
                {a.tags.map((t,j) => <span key={j} className="vx-agent-tag">{t}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Bento features ───────────────────────────────────────────────── */
function FeaturesSection() {
  const ref = useRef(null);
  useEffect(() => {
    gsap.fromTo(".vx-bc",
      { opacity:0, scale:.94 },
      { opacity:1, scale:1, duration:.5, stagger:.1, ease:"power2.out",
        scrollTrigger:{ trigger:ref.current, start:"top 78%", once:true } });
  }, []);
  return (
    <div className="vx-full-row vx-alt-bg" id="features">
      <div className="vx-section" ref={ref}>
        <div className="vx-sec-label">Capabilities</div>
        <h2 className="vx-sec-h2">Engineered to teach</h2>
        <p className="vx-sec-p">Every design decision is grounded in learning science, not just AI capability.</p>
        <div className="vx-bento">
          {BENTO.map((b,i) => (
            <div key={i} className={"vx-bc" + (b.span2 ? " span2" : "")}>
              <div className="vx-bc-icon" style={{background:b.bg}}>
                <i data-lucide={b.icon} style={{width:22,height:22,color:b.c}}/>
              </div>
              <div className="vx-bc-lbl" style={{color:b.c}}>{b.lbl}</div>
              {b.big && <div className="vx-bc-big">{b.big}</div>}
              <div className="vx-bc-title">{b.title}</div>
              <p className="vx-bc-desc">{b.desc}</p>
              {b.span2 && <div className="vx-bc-bar" style={{background:"linear-gradient(90deg,"+b.c+",transparent)"}}/>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── CTA ──────────────────────────────────────────────────────────── */
function CtaSection() {
  const ref = useRef(null);
  useEffect(() => {
    gsap.fromTo(ref.current,
      { opacity:0, y:40 },
      { opacity:1, y:0, duration:.7, ease:"power3.out",
        scrollTrigger:{ trigger:ref.current, start:"top 82%", once:true } });
  }, []);
  return (
    <div className="vx-cta-wrap" ref={ref}>
      <div className="vx-cta-box">
        <h2 className="vx-cta-h">Stop re-reading.<br/>Start understanding.</h2>
        <p className="vx-cta-p">Vaathiyar replaces passive study with active, adaptive dialogue. Your first session is free — no credit card required.</p>
        <div className="vx-cta-btns">
          <a href="register.html" className="vx-btn-primary" style={{padding:".85rem 2.1rem",fontSize:"1rem",borderRadius:11}}>
            Create Free Account
          </a>
          <a href="login.html" className="vx-btn-ghost" style={{padding:".85rem 2.1rem",fontSize:"1rem",borderRadius:11}}>
            Sign In →
          </a>
        </div>
      </div>
    </div>
  );
}

/* ── Footer ───────────────────────────────────────────────────────── */
function Footer() {
  return (
    <footer className="vx-footer">
      <div>
        <div className="vx-footer-brand">VAATHIYAR</div>
        <div className="vx-footer-sub">AI-Powered Education Platform</div>
      </div>
      <div className="vx-footer-copy">© 2026 Vaathiyar. All rights reserved.</div>
    </footer>
  );
}

/* ── App ──────────────────────────────────────────────────────────── */
function App() {
  useEffect(() => { lucide.createIcons(); });
  return (
    <>
      <Nav/>
      <Hero/>
      <div className="vx-sec-divider"/>
      <HowSection/>
      <div className="vx-sec-divider"/>
      <AgentsSection/>
      <div className="vx-sec-divider"/>
      <FeaturesSection/>
      <CtaSection/>
      <Footer/>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
</script>
{% endverbatim %}
</body>
</html>
"""

path = r"d:\final year project\V - Copy\backend\static_frontend\landing.html"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

lines = content.splitlines()
print(f"Written {len(lines)} lines to {path}")
import os
print(f"File size: {os.path.getsize(path):,} bytes")
