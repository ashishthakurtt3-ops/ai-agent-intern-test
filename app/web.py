from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .agent import SupportAgent
from .config import get_settings

app = FastAPI(title="Aster & Row Support")
_agent: SupportAgent | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web-default"


@app.on_event("startup")
def startup() -> None:
    global _agent
    _agent = SupportAgent(get_settings())


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return '''<!doctype html><html><head><meta charset="utf-8"><title>Aster & Row Support</title>
<style>body{font-family:Inter,system-ui,sans-serif;max-width:850px;margin:40px auto;padding:0 18px;background:#f6f7f9}h1{margin-bottom:8px}.sub{color:#667085}.card{background:white;border:1px solid #e4e7ec;border-radius:16px;padding:18px;box-shadow:0 6px 25px #10182810}#chat{min-height:420px;display:flex;flex-direction:column;gap:12px;margin-bottom:16px}.m{padding:12px 14px;border-radius:12px;white-space:pre-wrap}.u{align-self:flex-end;background:#111827;color:#fff;max-width:80%}.a{align-self:flex-start;background:#f2f4f7;max-width:85%}.row{display:flex;gap:8px}input{flex:1;padding:12px;border:1px solid #d0d5dd;border-radius:10px}button{padding:12px 16px;border:0;border-radius:10px;background:#111827;color:#fff;cursor:pointer}</style>
</head><body><h1>Aster & Row Support</h1><p class="sub">Grounded policy answers, safe order lookup, and multi-turn support.</p><div class="card"><div id="chat"></div><div class="row"><input id="msg" placeholder="Ask about returns, shipping, or an order…"/><button onclick="send()">Send</button></div></div>
<script>const sid=crypto.randomUUID();const chat=document.getElementById('chat');const input=document.getElementById('msg');function add(t,c){const d=document.createElement('div');d.className='m '+c;d.textContent=t;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}async function send(){const message=input.value.trim();if(!message)return;input.value='';add(message,'u');try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,session_id:sid})});const x=await r.json();add(x.answer+(x.handoff?'\n\nHuman support recommended.':''),'a')}catch(e){add('Unable to reach the support service.','a')}}input.addEventListener('keydown',e=>{if(e.key==='Enter')send()});</script></body></html>'''


@app.post("/chat")
def chat(req: ChatRequest):
    if _agent is None:
        raise RuntimeError("Agent is not initialized")
    return _agent.answer(req.message, req.session_id)
