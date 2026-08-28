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
    return '''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aster & Row Support</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#101828;background:#f5f7fa}
body{margin:0}.wrap{max-width:900px;margin:0 auto;padding:42px 18px 60px}.hero{margin-bottom:18px}.brand{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#667085}.hero h1{font-size:34px;line-height:1.1;margin:7px 0}.sub{color:#667085;margin:0}.card{background:#fff;border:1px solid #e4e7ec;border-radius:20px;padding:18px;box-shadow:0 14px 40px rgba(16,24,40,.08)}#chat{min-height:480px;max-height:62vh;overflow:auto;display:flex;flex-direction:column;gap:14px;margin-bottom:16px}.message{display:flex;flex-direction:column;gap:7px;max-width:86%}.message.user{align-self:flex-end}.message.assistant{align-self:flex-start}.bubble{padding:13px 15px;border-radius:15px;white-space:pre-wrap;line-height:1.5}.user .bubble{background:#101828;color:#fff}.assistant .bubble{background:#f2f4f7}.meta{font-size:12px;color:#667085}.sources{display:flex;flex-wrap:wrap;gap:6px}.source{font-size:11px;background:#eef2ff;border:1px solid #dbe4ff;border-radius:999px;padding:4px 8px}.handoff{font-size:12px;font-weight:600}.row{display:flex;gap:9px}input{flex:1;min-width:0;padding:13px 14px;border:1px solid #d0d5dd;border-radius:12px;font-size:15px}button{padding:13px 18px;border:0;border-radius:12px;background:#101828;color:#fff;font-weight:600;cursor:pointer}button:disabled{opacity:.5;cursor:default}.hint{font-size:12px;color:#98a2b3;margin:10px 2px 0}
</style></head>
<body><main class="wrap"><section class="hero"><div class="brand">Aster & Row</div><h1>Support, grounded in company data.</h1><p class="sub">Policy answers, safe order lookup, and context-aware follow-ups.</p></section>
<div class="card"><div id="chat"></div><div class="row"><input id="msg" aria-label="Message" placeholder="Ask about returns, shipping, or an order…"/><button id="send" onclick="send()">Send</button></div><div class="hint">Try: “Where is ORD-1007?” then “When will it arrive?”</div></div></main>
<script>
const sid=crypto.randomUUID();const chat=document.getElementById('chat');const input=document.getElementById('msg');const sendButton=document.getElementById('send');
function addUser(text){const wrap=document.createElement('div');wrap.className='message user';const b=document.createElement('div');b.className='bubble';b.textContent=text;wrap.appendChild(b);chat.appendChild(wrap)}
function addAssistant(x){const wrap=document.createElement('div');wrap.className='message assistant';const b=document.createElement('div');b.className='bubble';b.textContent=x.answer;wrap.appendChild(b);if(x.sources&&x.sources.length){const s=document.createElement('div');s.className='sources';x.sources.forEach(v=>{const t=document.createElement('span');t.className='source';t.textContent=v.filename+' — '+v.heading;s.appendChild(t)});wrap.appendChild(s)}if(x.handoff){const h=document.createElement('div');h.className='handoff';h.textContent='Human support recommended';wrap.appendChild(h)}chat.appendChild(wrap);chat.scrollTop=chat.scrollHeight}
async function send(){const message=input.value.trim();if(!message)return;input.value='';sendButton.disabled=true;addUser(message);try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,session_id:sid})});if(!r.ok)throw new Error('request failed');addAssistant(await r.json())}catch(e){addAssistant({answer:'Unable to reach the support service. Please check the server logs.',sources:[],handoff:true})}finally{sendButton.disabled=false;input.focus()}}
input.addEventListener('keydown',e=>{if(e.key==='Enter')send()});input.focus();
</script></body></html>'''


@app.post("/chat")
def chat(req: ChatRequest):
    if _agent is None:
        raise RuntimeError("Agent is not initialized")
    return _agent.answer(req.message, req.session_id)
