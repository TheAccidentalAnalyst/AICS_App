from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dataclasses import dataclass
from typing import List, Optional, Tuple
import json, re

app = FastAPI(title='SHAPE Session Prep — Minimal')

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

class Msg(BaseModel):
    role: str
    content: str

@dataclass
class ParsedChat:
    messages: List[Msg]
    errors: List[str]

ROLE_ALIASES = {'user': {'user','human','u','you'}, 'assistant': {'assistant','ai','bot','system','model'}}

def normalize_role(role: str) -> str:
    r = role.strip().lower()
    for canon, aliases in ROLE_ALIASES.items():
        if r in aliases:
            return canon
    return 'user'

def parse_json_chat(text: str) -> ParsedChat:
    try:
        data = json.loads(text)
        if isinstance(data, dict) and 'messages' in data:
            data = data['messages']
        if not isinstance(data, list):
            raise ValueError('JSON must be a list or {messages:[...]}')
        msgs = []
        for m in data:
            role = normalize_role(m.get('role','user'))
            content = m.get('content','')
            if isinstance(content, list):
                content = ' '.join(str(p) for p in content)
            msgs.append(Msg(role=role, content=str(content)))
        return ParsedChat(msgs, [])
    except Exception as e:
        return ParsedChat([], [f'JSON parse failed: {e}'])

USER_MARKERS = ['user:','human:','you:']
AI_MARKERS = ['assistant:','ai:','bot:','model:','system:']

def parse_plaintext_chat(text: str) -> ParsedChat:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    msgs: List[Msg] = []
    role: Optional[str] = None
    buf: List[str] = []

    def detect_role(line: str) -> Optional[str]:
        ll = line.lower().strip()
        for m in USER_MARKERS:
            if ll.startswith(m): return 'user'
        for m in AI_MARKERS:
            if ll.startswith(m): return 'assistant'
        return None

    for ln in lines:
        r = detect_role(ln)
        if r is not None:
            if buf and role:
                msgs.append(Msg(role=role, content='\n'.join(buf).strip()))
            role = r
            ln = re.sub(r'^\w+:\s*','', ln, flags=re.IGNORECASE)
            buf = [ln]
        else:
            buf.append(ln)
    if buf:
        msgs.append(Msg(role=role or 'user', content='\n'.join(buf).strip()))
    if not msgs:
        msgs = [Msg(role='user', content=text.strip())]
    return ParsedChat(msgs, [])

def parse_chat(text: str) -> ParsedChat:
    text = text.strip()
    if not text: return ParsedChat([], [])
    pj = parse_json_chat(text)
    if pj.messages: return pj
    return parse_plaintext_chat(text)

def word_count(s: str) -> int:
    return len(re.findall(r'\b\w+\b', s))

CODE_PATTERN = re.compile(r'```.+?```', re.DOTALL)

@dataclass
class SessionStats:
    turns: int
    user_turns: int
    ai_turns: int
    user_words: int
    ai_words: int
    ai_share: float
    has_code: bool

def extract_stats(msgs: List[Msg]) -> SessionStats:
    user_turns = sum(1 for m in msgs if m.role=='user')
    ai_turns = sum(1 for m in msgs if m.role=='assistant')
    user_words = sum(word_count(m.content) for m in msgs if m.role=='user')
    ai_words = sum(word_count(m.content) for m in msgs if m.role=='assistant')
    total = max(1, user_words + ai_words)
    ai_share = ai_words / total
    has_code = any(CODE_PATTERN.search(m.content) for m in msgs)
    return SessionStats(len(msgs), user_turns, ai_turns, user_words, ai_words, ai_share, bool(has_code))

def estimate_shape(stats: SessionStats) -> Tuple[int, List[str]]:
    score = 2
    reasons = []
    if stats.ai_share >= 0.65:
        score += 1; reasons.append('AI authored most of the words (≥65%).')
    if stats.turns > 12:
        score += 1; reasons.append('Longer, iterative session indicates AI guidance.')
    if stats.has_code:
        score += 1; reasons.append('AI produced code/structured blocks.')
    if stats.user_words / max(1, stats.user_words + stats.ai_words) > 0.6:
        score -= 1; reasons.append('Human authored most of the words (>60%).')
    score = max(0, min(5, score))
    return score, reasons

def shape_label(score: int) -> str:
    return {0:'Negligible AI influence',1:'Light AI influence',2:'Moderate AI influence',3:'Significant AI influence',4:'Major AI-guided changes',5:'AI-dominant shaping'}.get(score,'N/A')

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request, 'result': None})

@app.post('/analyze', response_class=HTMLResponse)
async def analyze(request: Request, transcript: str = Form(...)):
    parsed = parse_chat(transcript)
    if not parsed.messages:
        return templates.TemplateResponse('index.html', {'request': request, 'result': {'error':'Could not parse transcript.'}})
    stats = extract_stats(parsed.messages)
    score, reasons = estimate_shape(stats)
    result = {
        'stats': {'turns': stats.turns, 'user_turns': stats.user_turns, 'ai_turns': stats.ai_turns, 'human_words': stats.user_words, 'ai_words': stats.ai_words, 'ai_share': round(stats.ai_share,3), 'has_code': stats.has_code},
        'score': score,
        'label': shape_label(score),
        'reasons': reasons,
        'explanation': f'This gauges how much AI shaped your session—no final output required. AI wrote ~{round(stats.ai_share*100)}% of words across {stats.turns} turns ({stats.user_turns} human / {stats.ai_turns} AI). Use this as a starting point to reflect on your role.'
    }
    return templates.TemplateResponse('index.html', {'request': request, 'result': result})

@app.get('/health')
async def health():
    return {'status':'ok'}