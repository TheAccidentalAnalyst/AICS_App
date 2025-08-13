# optimized_aics_app.py

import re
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import docx
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import chardet # Library to detect character encoding

# --- App Setup ---
app = FastAPI(title="AICS Human-AI Collaboration Analyzer")
# Assumes the HTML file is in a 'templates' directory
templates = Jinja2Templates(directory="templates")

# --- Data Models ---

# 1. Replaced old CollaborationPattern with the new 4-tier system
class AIUseClassification(Enum):
    TOOL_ENHANCER = "Tool / Enhancer"
    ASSISTANT = "Assistant"
    AUGMENTOR = "Augmentor"
    COCREATOR = "Cocreator"

@dataclass
class Message:
    role: str
    content: str
    word_count: int

@dataclass
class ParsedSession:
    messages: List[Message]
    errors: List[str]
    user_word_count: int
    ai_word_count: int
    user_turns: int
    ai_turns: int

@dataclass
class CollaborationInsights:
    # Quantitative stats for the Light Report
    total_turns: int
    user_turns: int
    ai_turns: int
    user_words: int
    ai_words: int
    ai_contribution_ratio: float
    
    # Qualitative analysis for the Full Report
    structural_score: int
    human_meaning_score: int
    authorial_voice_score: int
    purpose_framing_score: int
    editorial_score: int
    total_shape_score: int
    
    # Final classification for both reports
    classification: AIUseClassification

# --- Parsing Logic ---

def parse_chat_transcript(text: str) -> ParsedSession:
    """
    Parses a raw text transcript into a list of messages.
    This version is simplified to focus on the core logic of splitting by speaker.
    """
    if not text or not text.strip():
        return ParsedSession([], ["Input text is empty."], 0, 0, 0, 0)

    # Normalize line endings
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # DEBUG FIX: Made the regex more specific to prevent potential ReDoS attacks.
    # It now looks for a newline, potential whitespace, the speaker role, a colon, and then more whitespace.
    parts = re.split(r'\n\s*(?=(?:User|You|Human|AI|Assistant|ChatGPT):\s*)', text.strip())
    
    messages = []
    errors = []
    
    user_word_count = 0
    ai_word_count = 0
    user_turns = 0
    ai_turns = 0

    if len(parts) == 1 and '\n' not in text:
        parts = [text]

    current_role = "user" 
    
    for part in parts:
        part = part.strip()
        if not part:
            continue

        part_lower = part.lower()
        role = current_role
        
        if any(part_lower.startswith(p) for p in ["user:", "you:", "human:"]):
            role = "user"
            part = re.sub(r'^(?:User|You|Human):\s*', '', part, flags=re.IGNORECASE).strip()
        elif any(part_lower.startswith(p) for p in ["ai:", "assistant:", "chatgpt:"]):
            role = "assistant"
            part = re.sub(r'^(?:AI|Assistant|ChatGPT):\s*', '', part, flags=re.IGNORECASE).strip()
        
        word_count = len(re.findall(r'\b\w+\b', part))
        messages.append(Message(role=role, content=part, word_count=word_count))
        
        if role == "user":
            user_word_count += word_count
            user_turns += 1
            current_role = "assistant"
        else:
            ai_word_count += word_count
            ai_turns += 1
            current_role = "user"

    if not messages:
        errors.append("Could not parse transcript. Please ensure it contains clear speaker roles (e.g., 'User:' and 'AI:').")

    return ParsedSession(messages, errors, user_word_count, ai_word_count, user_turns, ai_turns)


# --- Analysis Engine ---

def calculate_shape_scores(messages: List[Message]) -> Tuple[int, int, int, int, int]:
    """Calculate SHAPE scores based on user prompts."""
    user_messages = [m.content.lower() for m in messages if m.role == "user"]
    if not user_messages:
        return 0, 0, 0, 0, 0

    # S - Structural Vision
    s_score = sum(1 for m in user_messages if any(k in m for k in ["outline", "structure", "organize", "framework", "reorganize", "format"]))
    
    # H - Human-Led Meaning
    h_score = sum(1 for m in user_messages if any(k in m for k in ["meaning", "interpret", "clarify", "the point is", "in other words"]))
    
    # A - Authorial Voice
    a_score = sum(1 for m in user_messages if any(k in m for k in ["my voice", "style", "tone", "make it sound like", "more personal"]))
    
    # P - Purpose Framing
    p_score = sum(1 for m in user_messages if any(k in m for k in ["audience", "purpose", "goal", "for a", "so that"]))
    
    # E - Editorial Intervention
    e_score = sum(1 for m in user_messages if any(k in m for k in ["edit", "refine", "change", "add", "remove", "improve", "rewrite"]))

    # Clamp scores between 0 and 5
    return min(s_score, 5), min(h_score, 5), min(a_score, 5), min(p_score, 5), min(e_score, 5)

# 2. New function to determine classification based on SHAPE score
def determine_ai_use_classification(total_shape_score: int) -> AIUseClassification:
    """Determines the classification based on the total SHAPE score."""
    if total_shape_score <= 10:
        return AIUseClassification.TOOL_ENHANCER
    elif 11 <= total_shape_score <= 17:
        return AIUseClassification.ASSISTANT
    elif 18 <= total_shape_score <= 22:
        return AIUseClassification.AUGMENTOR
    else: # 23-25
        return AIUseClassification.COCREATOR

# 3. Updated recommendations to match the new classification system
def generate_recommendations(classification: AIUseClassification) -> Dict[str, Any]:
    """Generates recommendations based on the user's classification."""
    recs = {
        AIUseClassification.TOOL_ENHANCER: {
            "title": "Your Path to Assistant",
            "summary": "You're using AI for specific tasks. To grow, try giving the AI more open-ended problems to solve.",
            "tactics": [
                "Ask the AI for a full first draft instead of just a small piece.",
                "Request multiple different versions or approaches to a problem.",
                "Provide more context about your audience and goal in your initial prompt."
            ]
        },
        AIUseClassification.ASSISTANT: {
            "title": "Your Path to Augmentor",
            "summary": "You're good at refining AI output. To advance, focus on providing more strategic direction *before* the AI generates.",
            "tactics": [
                "Define a clear structure or outline for the AI to follow.",
                "Ask the AI to critique its own work or identify weaknesses in its response.",
                "Specify a clear tone, style, and voice for the AI to adopt."
            ]
        },
        AIUseClassification.AUGMENTOR: {
            "title": "Your Path to Cocreator",
            "summary": "You are effectively guiding the AI with strong strategic input. To reach the next level, push the AI to become a true thinking partner.",
            "tactics": [
                "Challenge the AI's assumptions by asking 'What are the flaws in this approach?'.",
                "Use the AI for more creative, divergent thinking: 'Brainstorm three unconventional solutions.'",
                "Delegate comparative analysis: 'How does this plan compare to successful examples in other fields?'"
            ]
        },
        AIUseClassification.COCREATOR: {
            "title": "You are a Cocreator!",
            "summary": "You are operating at the highest level of human-AI collaboration, using the AI as a true strategic partner. Keep exploring the boundaries of what's possible.",
            "tactics": [
                "Continue to push the AI into novel domains and complex, multi-step reasoning tasks.",
                "Experiment with having the AI adopt multiple expert personas to debate a topic.",
                "Use the AI to synthesize information from completely different fields to spark innovation."
            ]
        }
    }
    return recs.get(classification, {})

def analyze_session(session: ParsedSession) -> CollaborationInsights:
    """Performs the full analysis of the parsed session."""
    s, h, a, p, e = calculate_shape_scores(session.messages)
    total_shape = s + h + a + p + e
    
    classification = determine_ai_use_classification(total_shape)
    
    total_words = max(1, session.user_word_count + session.ai_word_count)
    ai_contribution_ratio = session.ai_word_count / total_words
    
    return CollaborationInsights(
        total_turns=session.user_turns + session.ai_turns,
        user_turns=session.user_turns,
        ai_turns=session.ai_turns,
        user_words=session.user_word_count,
        ai_words=session.ai_word_count,
        ai_contribution_ratio=ai_contribution_ratio,
        structural_score=s,
        human_meaning_score=h,
        authorial_voice_score=a,
        purpose_framing_score=p,
        editorial_score=e,
        total_shape_score=total_shape,
        classification=classification
    )

# --- FastAPI Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serves the main page."""
    return templates.TemplateResponse("enhanced_html_template.html", {"request": request, "result": None})

# 4. Modified /analyze endpoint to handle the Freemium logic
@app.post("/analyze", response_class=HTMLResponse)
async def handle_analysis(
    request: Request,
    transcript_paste: str = Form(""),
    transcript_file: Optional[UploadFile] = File(None),
    email: Optional[str] = Form(None)
):
    """
    Analyzes the transcript and returns either a Light or Full report
    based on the presence of an email address.
    """
    text_content = transcript_paste
    errors = []

    if transcript_file and transcript_file.filename:
        try:
            contents = await transcript_file.read()
            # DEBUG FIX: Handle different file encodings gracefully.
            # First, try to detect the encoding. Fallback to utf-8.
            detected_encoding = chardet.detect(contents)['encoding'] or 'utf-8'
            
            if transcript_file.filename.endswith('.docx'):
                # python-docx reads from a file-like object, so we pass the file pointer
                transcript_file.file.seek(0)
                document = docx.Document(transcript_file.file)
                text_content = "\n".join([para.text for para in document.paragraphs])
            else:
                text_content = contents.decode(detected_encoding, errors='ignore')
        except Exception as e:
            errors.append(f"Error reading file: {e}")
    
    if not text_content and not errors:
        errors.append("Please upload a file or paste a transcript.")

    if errors:
        return templates.TemplateResponse("enhanced_html_template.html", {"request": request, "result": {"errors": errors}})

    session = parse_chat_transcript(text_content)
    
    if session.errors:
        return templates.TemplateResponse("enhanced_html_template.html", {"request": request, "result": {"errors": session.errors}})

    insights = analyze_session(session)
    
    # Freemium Gate Logic
    is_light_report = not bool(email and "@" in email)
    
    result = {
        "insights": insights,
        "is_light_report": is_light_report,
        "transcript_content": text_content, # Pass content back for the email form
        "errors": []
    }

    if not is_light_report:
        # Add full recommendations only for the full report
        result["recommendations"] = generate_recommendations(insights.classification)

    return templates.TemplateResponse("enhanced_html_template.html", {"request": request, "result": result})
