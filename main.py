import re
import json
from typing import List, Optional, Tuple
from dataclasses import dataclass

import docx
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# --- App Setup ---
app = FastAPI(title="SHAPE Session Analyzer")
templates = Jinja2Templates(directory="templates")

# --- Data Models ---
class Msg(BaseModel):
    role: str
    content: str

@dataclass
class ParsedChat:
    messages: List[Msg]
    errors: List[str]

# --- Parsing Logic ---
def parse_chat_transcript(text: str) -> ParsedChat:
    """
    Parses a raw text transcript that uses "You said:" and "ChatGPT said:" as delimiters.
    This is tailored to the user's manual copy-paste workflow.
    """
    if not text or not text.strip():
        return ParsedChat([], ["Input text is empty."])

    # Split by the most reliable markers
    # The (?=...) is a lookahead that keeps the delimiter in the result
    parts = re.split(r'(?=You said:|ChatGPT said:)', text.strip())
    
    messages: List[Msg] = []
    errors: List[str] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part.startswith("You said:"):
            role = "user"
            content = part.replace("You said:", "").strip()
        elif part.startswith("ChatGPT said:"):
            role = "assistant"
            content = part.replace("ChatGPT said:", "").strip()
        else:
            # Handle text before the first delimiter, assign it to the user
            if not messages:
                role = "user"
                content = part
            else:
                # If there's text that doesn't match, append it to the last message
                if messages:
                    messages[-1].content += f"\n\n{part}"
                continue
        
        if content:
            messages.append(Msg(role=role, content=content))

    if not messages:
        errors.append("Could not parse any conversational turns. Ensure the transcript uses 'You said:' and 'ChatGPT said:'.")

    return ParsedChat(messages=messages, errors=errors)

# --- SHAPE Analysis & Recommendations ---
@dataclass
class SessionStats:
    turns: int
    user_turns: int
    ai_turns: int
    user_words: int
    ai_words: int
    ai_share: float

def extract_stats(msgs: List[Msg]) -> SessionStats:
    user_turns = sum(1 for m in msgs if m.role == "user")
    ai_turns = sum(1 for m in msgs if m.role == "assistant")
    
    word_count = lambda s: len(re.findall(r'\b\w+\b', s))
    user_words = sum(word_count(m.content) for m in msgs if m.role == "user")
    ai_words = sum(word_count(m.content) for m in msgs if m.role == "assistant")
    
    total_words = max(1, user_words + ai_words)
    ai_share = ai_words / total_words

    return SessionStats(len(msgs), user_turns, ai_turns, user_words, ai_words, ai_share)

def get_shape_score_and_recs(stats: SessionStats) -> Tuple[int, str, str]:
    score = 2  # Start with a moderate baseline

    if stats.ai_share >= 0.65:
        score += 2
    elif stats.ai_share >= 0.40:
        score += 1

    if stats.ai_share <= 0.20:
        score -= 1
    
    if stats.turns > 20: # Long conversations suggest deeper collaboration or guidance
        score += 1
    
    score = max(0, min(5, score)) # Clamp score between 0 and 5

    interpretations = {
        0: "You were the sole author, using the AI as a basic tool (like a search engine or thesaurus).",
        1: "You heavily directed the session, using the AI for specific, small tasks.",
        2: "This was a balanced partnership where you provided clear direction and the AI generated content.",
        3: "The AI acted as a strong assistant, generating significant portions of the content based on your prompts.",
        4: "The AI did most of the heavy lifting, acting as a primary author with your guidance.",
        5: "The AI was the dominant author, generating nearly all of the content with minimal changes from you."
    }

    recommendations = {
        0: "To better leverage the AI, try asking it to create a full first draft or brainstorm a list of unconventional ideas to give you a stronger starting point.",
        1: "To deepen the collaboration, consider giving the AI more open-ended tasks. For example, ask it to 'propose a structure for this document' or 'expand on this key idea'.",
        2: "This is a great collaborative balance. To push further, ask the AI to critique its own work or act as a 'devil's advocate' to challenge your assumptions.",
        3: "You are effectively delegating tasks to the AI. To increase your own authorial contribution, try rewriting a key section entirely in your own voice or adding a unique analysis.",
        4: "To ensure the final work reflects your unique perspective, focus on adding personal insights, examples, or a critical analysis that the AI could not have produced on its own.",
        5: "This is a valid use of AI for rapid generation. However, be sure to thoroughly review, fact-check, and edit the output to ensure it meets your standards and contains your authorial voice."
    }
    
    return score, interpretations.get(score, ""), recommendations.get(score, "")

# --- FastAPI Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    transcript_paste: str = Form(None),
    transcript_file: Optional[UploadFile] = File(None)
):
    text_content = ""
    errors = []

    if transcript_file and transcript_file.filename:
        try:
            if transcript_file.filename.endswith('.docx'):
                document = docx.Document(transcript_file.file)
                text_content = "\n".join([para.text for para in document.paragraphs])
            else: # Assume .txt or other plain text
                contents = await transcript_file.read()
                text_content = contents.decode('utf-8')
        except Exception as e:
            errors.append(f"Error reading file: {e}")
    elif transcript_paste and transcript_paste.strip():
        text_content = transcript_paste
    else:
        errors.append("Please upload a file or paste a transcript.")

    if errors:
        return templates.TemplateResponse("index.html", {"request": request, "result": {"errors": errors}})

    parsed = parse_chat_transcript(text_content)
    
    if parsed.errors or not parsed.messages:
        return templates.TemplateResponse("index.html", {"request": request, "result": {"errors": parsed.errors or ["Failed to parse transcript."]}})
        
    stats = extract_stats(parsed.messages)
    score, interpretation, recommendation = get_shape_score_and_recs(stats)

    result = {
        "stats": stats,
        "score": score,
        "interpretation": interpretation,
        "recommendation": recommendation,
        "errors": []
    }

    return templates.TemplateResponse("index.html", {"request": request, "result": result})

@app.get("/health")
async def health():
    return {"status": "ok"}