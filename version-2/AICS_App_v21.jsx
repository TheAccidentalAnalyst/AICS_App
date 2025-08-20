import React, { useReducer, useRef, useEffect } from 'react';
import {
  BarChart3, Upload, CheckCircle, AlertCircle, FileText, MessageSquare,
  Brain, Eye, Edit3, Compass, Lightbulb, X, Target
} from 'lucide-react';

/* ============================================================================
   SHAPE Analysis (equal-weight heuristics)
   - Processes raw transcript text or [{role,text}] JSON
   - Scores SHAPE using an equal-weight rubric
   - Analyzes conversation patterns
   - Produces insights & actionable recommendations
   ---------------------------------------------------------------------------
   No external deps. Works in JS.
   ========================================================================== */

// SHAPE Analysis Functions
function parseTranscript(input) {
  if (Array.isArray(input)) return input;

  const raw = input.replace(/\r/g, '').trim();

  // Try JSON first
  if (/^\s*\[/.test(raw)) {
    try {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) {
        return arr
          .filter((x) => x && x.text != null)
          .map((x) => ({
            role: String((x.role || 'user')).toLowerCase(),
            text: String(x.text || '')
          }));
      }
    } catch { /* fall through to speaker-labeled */ }
  }

  // Fallback: "User: ...\nAssistant: ..." style
  const speakerMap = {
    user: 'user', you: 'user', human: 'user', me: 'user', customer: 'user',
    assistant: 'assistant', ai: 'assistant', chatgpt: 'assistant', model: 'assistant',
    system: 'system', tool: 'tool'
  };

  const lines = raw.split(/\n+/);
  const out = [];
  let current = null;

  const flush = () => { if (current && current.text.trim()) out.push(current); };

  for (const line of lines) {
    const m = line.match(/^\s*([A-Za-z ]+)\s*[:>-]\s*(.*)$/);
    if (m) {
      const label = m[1].toLowerCase().trim();
      const role = speakerMap[label] || (label.includes('user') ? 'user' : 'assistant');
      flush();
      current = { role, text: m[2] ?? '' };
    } else {
      if (!current) current = { role: 'user', text: '' };
      current.text += (current.text ? '\n' : '') + line;
    }
  }
  flush();
  return out;
}

const wordCount = (s) => (s.trim().match(/\b[\w'-]+\b/g) || []).length;
const avg = (nums) => (nums.length ? nums.reduce((a,b)=>a+b,0)/nums.length : 0);
const snippet = (text, start = 0, span = 120) => {
  const s = Math.max(0, start - 20);
  const e = Math.min(text.length, start + span);
  return text.slice(s, e).replace(/\s+/g, ' ').trim();
};

// SHAPE Pattern Definitions
const PAT = {
  S: [
    /\b(outline|table of contents|toc|heading|headings)\b/i,
    /\b(reorder|re[- ]?organize|move .* to|swap (sections|order))\b/i,
    /\b(flow|structure|organization|scaffold)\b/i,
    /^\s*\d+[.)]\s.+/m,           // numbered list
    /^\s*[-*]\s.+/m               // bulleted list
  ],
  H: [
    /\b(for example|e\.g\.|for instance|example:)\b/i,
    /\bwe define|definition:|means that\b/i,
    /\bthat means|the implication|we conclude\b/i,
    /\b(in my|in our)\s+(experience|research|context|company|team)\b/i,
    /\breframe|another way to see|let'?s frame\b/i
  ],
  A: [
    /\b(in my voice|my tone|my style|sounds like me)\b/i,
    /\b(use|with)\s+a\s+(warm|formal|conversational|playful|technical)\s+tone\b/i,
    /\bavoid\b.+\b(jargon|buzzwords|fluff)\b/i,
    /\bI would say|I'?d phrase it|let me rewrite|here'?s my rewrite\b/i,
    /\b(first person|third person|active voice|passive voice)\b/i
  ],
  P: [
    /\b(goal|objective|purpose|why)\b/i,
    /\baudience\b|for (teachers|executives|students|customers)\b/i,
    /\bI need\b.+\b(report|email|post|slides|outline|plan|brief)\b/i,
    /\b(length|word count|time limit|deadline|by (EOD|end of day|Friday))\b/i,
    /\bsuccess looks like|acceptance criteria|done when|must include\b/i
  ],
  E: [
    /\bthat('?s)? (wrong|incorrect|not right|not accurate)\b/i,
    /\b(correct|fix|revise|rewrite|tighten|clarify)\b/i,
    /\b(this is missing|add more|go deeper|elaborate)\b/i,
    /\bremove\b.+\b(section|part|paragraph|sentence)\b/i,
    /\bchange the emphasis|let'?s focus on\b/i
  ]
};

function evaluateDomain(messages, domain) {
  const userTurns = messages.map((m, i) => ({ m, i })).filter(x => x.m.role === 'user');
  const patterns = PAT[domain];
  const hitFlags = new Array(patterns.length).fill(false);
  const evidence = [];

  for (let p = 0; p < patterns.length; p++) {
    const rx = patterns[p];
    for (const { m, i } of userTurns) {
      const match = m.text.match(rx);
      if (match) {
        if (!hitFlags[p]) {
          evidence.push({ pattern: rx.source, text: snippet(m.text, match.index ?? 0), turnIndex: i });
        }
        hitFlags[p] = true;
        break; // next pattern
      }
    }
  }

  const hits = hitFlags.filter(Boolean).length; // 0..5
  const score = Math.round((hits / patterns.length) * 20); // steps of 4
  return { score, hits, max: patterns.length, evidence };
}

function scoreSHAPE(input) {
  const messages = parseTranscript(input);
  const S = evaluateDomain(messages, 'S');
  const H = evaluateDomain(messages, 'H');
  const A = evaluateDomain(messages, 'A');
  const P = evaluateDomain(messages, 'P');
  const E = evaluateDomain(messages, 'E');
  return { S, H, A, P, E, total: S.score + H.score + A.score + P.score + E.score };
}

function analyzeTranscriptPatterns(messages) {
  const turns = messages.length;
  const users = messages.filter(m => m.role === 'user');
  const assistants = messages.filter(m => m.role === 'assistant');

  const userWords = users.map(m => wordCount(m.text));
  const assistantWords = assistants.map(m => wordCount(m.text));
  const totalUser = userWords.reduce((a,b)=>a+b,0);
  const totalAssistant = assistantWords.reduce((a,b)=>a+b,0);
  const total = totalUser + totalAssistant || 1;

  // early purpose check: first 3 user turns
  const first3User = users.slice(0, 3).map(u => u.text).join('\n');
  const startedWithPurpose = !!first3User.match(PAT.P[0]) || !!first3User.match(PAT.P[1]) || !!first3User.match(PAT.P[4]);

  // outline present anywhere?
  const usedOutline = messages.some(m => PAT.S[0].test(m.text) || PAT.S[3].test(m.text) || PAT.S[4].test(m.text));

  return {
    turns,
    userTurns: users.length,
    assistantTurns: assistants.length,
    avgUserWords: Math.round(avg(userWords)),
    avgAssistantWords: Math.round(avg(assistantWords)),
    userShareOfWords: +(totalUser / total).toFixed(3),
    startedWithPurpose,
    usedOutline
  };
}

function generateInsightsAndRecommendations(scores, stats) {
  const insights = [];
  const recs = [];

  // Domain-specific observations based on missing heuristics
  const noteIfLow = (key, label, suggestions) => {
    const ds = scores[key];
    if (ds.hits === 0) {
      insights.push({ domain: key, finding: `${label}: no clear signals detected.` });
      recs.push(...suggestions);
    } else if (ds.hits <= 2) {
      insights.push({ domain: key, finding: `${label}: limited signals (${ds.hits}/5).` });
      recs.push(...suggestions.slice(0, 2));
    }
  };

  noteIfLow('S', 'Structural Vision', [
    'Start with a quick outline or headings.',
    'Ask the model to reorder sections or improve flow.',
    'Use bullets/numbered lists to scaffold the piece.'
  ]);

  noteIfLow('H', 'Human-Led Meaning', [
    'Add an example from your context (team, org, class).',
    'Define key terms in your own words and state implications.',
    'Reframe the idea ("another way to see this is…").'
  ]);

  noteIfLow('A', 'Authorial Voice', [
    'State the tone you want (e.g., warm, formal, technical).',
    'Rewrite one paragraph in your own words and ask the model to match.',
    'Tell the model to avoid jargon/buzzwords.'
  ]);

  noteIfLow('P', 'Purpose Framing', [
    'Open with your goal, audience, and desired deliverable ("I need a 1-page brief for executives").',
    'Specify any constraints (length, deadline) and what success looks like.'
  ]);

  noteIfLow('E', 'Editorial Intervention', [
    'Point out what is wrong or missing and say how to fix it.',
    'Ask for deeper detail or remove sections that aren't helpful.'
  ]);

  // Conversation pattern tips
  if (!stats.startedWithPurpose) {
    insights.push({ domain: 'P', finding: 'Purpose cues not stated early (first 3 user turns).' });
    recs.push('Begin the session by stating goal, audience, and desired output.');
  }
  if (!stats.usedOutline && scores.S.hits === 0) {
    insights.push({ domain: 'S', finding: 'No outline or scaffolding detected.' });
    recs.push('Add a quick outline or bullet scaffold before drafting.');
  }

  // De-duplicate recommendations while keeping order
  const deduped = Array.from(new Set(recs));

  return { insights, recommendations: deduped };
}

function analyzeSHAPE(input) {
  const messages = parseTranscript(input);
  const scores = scoreSHAPE(messages);
  const stats = analyzeTranscriptPatterns(messages);
  const { insights, recommendations } = generateInsightsAndRecommendations(scores, stats);
  return { scores, stats, insights, recommendations };
}

// Action types for state management
const ACTION_TYPES = {
  SET_INPUT_METHOD: 'SET_INPUT_METHOD',
  SET_TRANSCRIPT: 'SET_TRANSCRIPT',
  SET_FILE: 'SET_FILE',
  SET_EMAIL: 'SET_EMAIL',
  SET_EMAIL_CONSENT: 'SET_EMAIL_CONSENT',
  SET_ANALYSIS_STATE: 'SET_ANALYSIS_STATE',
  ADD_MESSAGE: 'ADD_MESSAGE',
  SET_RESULT: 'SET_RESULT',
  SHOW_MODAL: 'SHOW_MODAL',
  HIDE_MODAL: 'HIDE_MODAL',
  RESET_ALL: 'RESET_ALL',
  CLEAR_MESSAGES: 'CLEAR_MESSAGES',
  UNLOCK_FULL_REPORT: 'UNLOCK_FULL_REPORT'
};

// Initial state
const initialState = {
  inputMethod: '',
  transcript: '',
  file: null,
  email: '',
  emailConsent: false,
  isAnalyzing: false,
  analysisMessages: [],
  result: null,
  showFullReport: false,
  modal: {
    isOpen: false,
    type: 'info', // 'info', 'confirm', 'error'
    title: '',
    message: '',
    onConfirm: null,
    onCancel: null
  }
};

// Reducer function
function appReducer(state, action) {
  switch (action.type) {
    case ACTION_TYPES.SET_INPUT_METHOD:
      return { ...state, inputMethod: action.payload };

    case ACTION_TYPES.SET_TRANSCRIPT:
      return { ...state, transcript: action.payload };

    case ACTION_TYPES.SET_FILE:
      return { ...state, file: action.payload };

    case ACTION_TYPES.SET_EMAIL:
      return { ...state, email: action.payload };

    case ACTION_TYPES.SET_EMAIL_CONSENT:
      return { ...state, emailConsent: action.payload };

    case ACTION_TYPES.SET_ANALYSIS_STATE:
      return { ...state, isAnalyzing: action.payload };

    case ACTION_TYPES.ADD_MESSAGE:
      return {
        ...state,
        analysisMessages: [
          ...state.analysisMessages,
          {
            id: Date.now() + Math.random(),
            content: action.payload.content,
            sender: action.payload.sender,
            timestamp: new Date()
          }
        ]
      };

    case ACTION_TYPES.SET_RESULT:
      return { ...state, result: action.payload };

    case ACTION_TYPES.SHOW_MODAL:
      return {
        ...state,
        modal: {
          isOpen: true,
          type: action.payload.type || 'info',
          title: action.payload.title || '',
          message: action.payload.message || '',
          onConfirm: action.payload.onConfirm || null,
          onCancel: action.payload.onCancel || null
        }
      };

    case ACTION_TYPES.HIDE_MODAL:
      return { ...state, modal: { ...initialState.modal } };

    case ACTION_TYPES.CLEAR_MESSAGES:
      return { ...state, analysisMessages: [] };

    case ACTION_TYPES.UNLOCK_FULL_REPORT:
      return { ...state, showFullReport: true };

    case ACTION_TYPES.RESET_ALL:
      return { ...initialState };

    default:
      return state;
  }
}

// Modal Component
const Modal = ({ modal, dispatch }) => {
  if (!modal.isOpen) return null;

  const handleConfirm = () => {
    if (modal.onConfirm) modal.onConfirm();
    dispatch({ type: ACTION_TYPES.HIDE_MODAL });
  };

  const handleCancel = () => {
    if (modal.onCancel) modal.onCancel();
    dispatch({ type: ACTION_TYPES.HIDE_MODAL });
  };

  const getModalStyles = () => {
    switch (modal.type) {
      case 'error':
        return 'border-red-200 bg-red-50';
      case 'confirm':
        return 'border-orange-200 bg-orange-50';
      default:
        return 'border-gray-200 bg-white';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`max-w-md w-full rounded-lg border-2 p-6 shadow-xl ${getModalStyles()}`}>
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{modal.title}</h3>
          <button
            onClick={() => dispatch({ type: ACTION_TYPES.HIDE_MODAL })}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-gray-700 mb-6">{modal.message}</p>

        <div className="flex gap-3 justify-end">
          {modal.type === 'confirm' && (
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleConfirm}
            className={`px-4 py-2 rounded-lg transition-colors ${
              modal.type === 'error'
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-orange-500 hover:bg-orange-600 text-white'
            }`}
          >
            {modal.type === 'confirm' ? 'Confirm' : 'OK'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Input Panel Component
const InputPanel = ({ state, dispatch, fileInputRef }) => {
  const PASTE_CHAR_LIMIT = 50000;
  const PASTE_WARN_LIMIT = 40000;

  const isOverLimit = state.transcript.length > PASTE_CHAR_LIMIT;
  const isNearLimit = state.transcript.length > PASTE_WARN_LIMIT;

  const handleFileUpload = async (event) => {
    const uploadedFile = event.target.files[0];
    if (!uploadedFile) return;

    const lower = uploadedFile.name.toLowerCase();
    if (!(lower.endsWith('.txt') || lower.endsWith('.md'))) {
      dispatch({
        type: ACTION_TYPES.SHOW_MODAL,
        payload: {
          type: 'error',
          title: 'Unsupported File',
          message: 'Please upload a .txt or .md file, or use the Paste Text option.'
        }
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    try {
      dispatch({ type: ACTION_TYPES.SET_FILE, payload: uploadedFile });

      const reader = new FileReader();
      const extractedText = await new Promise((resolve, reject) => {
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(uploadedFile);
      });

      dispatch({ type: ACTION_TYPES.SET_TRANSCRIPT, payload: extractedText });
    } catch (error) {
      dispatch({
        type: ACTION_TYPES.SHOW_MODAL,
        payload: {
          type: 'error',
          title: 'File Upload Error',
          message: 'Failed to read the file. Please try again with a different file.'
        }
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleInputMethodChange = (newMethod) => {
    const hasContent = state.transcript.trim() || state.file;

    if (hasContent && newMethod !== state.inputMethod) {
      dispatch({
        type: ACTION_TYPES.SHOW_MODAL,
        payload: {
          type: 'confirm',
          title: 'Switch Input Method',
          message: 'Switching input methods will clear your current content. Are you sure?',
          onConfirm: () => {
            dispatch({ type: ACTION_TYPES.SET_TRANSCRIPT, payload: '' });
            dispatch({ type: ACTION_TYPES.SET_FILE, payload: null });
            dispatch({ type: ACTION_TYPES.SET_INPUT_METHOD, payload: newMethod });
            if (fileInputRef.current) fileInputRef.current.value = '';
          }
        }
      });
    } else {
      dispatch({ type: ACTION_TYPES.SET_INPUT_METHOD, payload: newMethod });
    }
  };

  const clearFile = () => {
    dispatch({ type: ACTION_TYPES.SET_FILE, payload: null });
    dispatch({ type: ACTION_TYPES.SET_TRANSCRIPT, payload: '' });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const truncateFileName = (fileName, maxLength = 30) => {
    if (fileName.length <= maxLength) return fileName;
    const extension = fileName.split('.').pop();
    const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.'));
    const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 4) + '...';
    return `${truncatedName}.${extension}`;
  };

  return (
    <div className="w-1/2 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center mr-3">
            <BarChart3 className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AICS Input</h1>
        </div>
        <p className="text-gray-600">Choose how to provide your chat transcript for analysis</p>
      </div>

      <div className="p-6 flex-1">
        {/* Input Method Selection */}
        <div className="mb-6">
          <div className="grid grid-cols-2 gap-3 mb-4">
            <button
              onClick={() => handleInputMethodChange('upload')}
              className={`p-4 rounded-lg border-2 flex flex-col items-center transition-all ${
                state.inputMethod === 'upload'
                  ? 'border-orange-500 bg-orange-50 text-orange-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <Upload className="h-6 w-6 mb-2" />
              <span className="text-sm font-medium">Upload File</span>
              <span className="text-xs text-gray-500 mt-1">Text or Markdown only</span>
            </button>
            <button
              onClick={() => handleInputMethodChange('paste')}
              className={`p-4 rounded-lg border-2 flex flex-col items-center transition-all ${
                state.inputMethod === 'paste'
                  ? 'border-orange-500 bg-orange-50 text-orange-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <FileText className="h-6 w-6 mb-2" />
              <span className="text-sm font-medium">Paste Text</span>
              <span className="text-xs text-gray-500 mt-1">Copy & paste directly</span>
            </button>
          </div>
        </div>

        {/* Upload Method */}
        {state.inputMethod === 'upload' && (
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Upload a .txt or .md Conversation</h3>

            {!state.file ? (
              <div>
                <button
                  onClick={triggerFileUpload}
                  className="w-full border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-orange-400 transition-colors cursor-pointer bg-white hover:bg-orange-50"
                >
                  <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <span className="text-gray-600 block">Click to upload your conversation file</span>
                  <div className="text-xs text-gray-500 mt-2">Supported: .txt (Text), .md (Markdown)</div>
                </button>

                <input
                  type="file"
                  accept=".txt,.md"
                  onChange={handleFileUpload}
                  className="hidden"
                  ref={fileInputRef}
                />
              </div>
            ) : (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center min-w-0 flex-1">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2 flex-shrink-0" />
                    <span className="text-green-800 font-medium truncate" title={state.file.name}>
                      {truncateFileName(state.file.name)}
                    </span>
                  </div>
                  <button
                    onClick={clearFile}
                    className="ml-2 text-sm bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded transition-colors flex-shrink-0"
                  >
                    Remove
                  </button>
                </div>
                <div className="text-sm text-green-600">
                  File loaded successfully ({Math.round(state.file.size / 1024)}KB)
                </div>
              </div>
            )}
          </div>
        )}

        {/* Paste Method */}
        {state.inputMethod === 'paste' && (
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Paste Your Conversation</h3>

            <div className="relative">
              <textarea
                value={state.transcript}
                onChange={(e) => dispatch({ type: ACTION_TYPES.SET_TRANSCRIPT, payload: e.target.value })}
                maxLength={PASTE_CHAR_LIMIT + 1000}
                placeholder={`Paste your conversation here...

Supported formats:
• You said: ... ChatGPT said: ...
• User: ... Assistant: ...
• Human: ... AI: ...

Example:
You said: Help me create a marketing strategy
ChatGPT said: I'd be happy to help you develop a comprehensive marketing strategy...`}
                className={`w-full h-64 p-4 border rounded-lg resize-none focus:ring-2 focus:border-transparent font-mono text-sm ${
                  isOverLimit
                    ? 'border-red-500 focus:ring-red-200'
                    : isNearLimit
                    ? 'border-yellow-500 focus:ring-yellow-200'
                    : 'border-gray-300 focus:ring-orange-200'
                }`}
              />
              
              {isOverLimit && (
                <div className="absolute bottom-2 right-2 text-red-600 text-xs bg-red-50 px-2 py-1 rounded">
                  Character limit exceeded
                </div>
              )}
              
              {isNearLimit && !isOverLimit && (
                <div className="absolute bottom-2 right-2 text-yellow-600 text-xs bg-yellow-50 px-2 py-1 rounded">
                  Near character limit
                </div>
              )}
              
              <div className="text-xs text-gray-500 mt-2 text-right">
                {state.transcript.length} / {PASTE_CHAR_LIMIT} characters
              </div>
            </div>
          </div>
        )}

        {/* Email Collection */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-3">Get Your Full Report</h3>
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="emailConsent"
                checked={state.emailConsent}
                onChange={(e) => dispatch({ type: ACTION_TYPES.SET_EMAIL_CONSENT, payload: e.target.checked })}
                className="mr-2"
              />
              <label htmlFor="emailConsent" className="text-sm text-gray-700">
                I want to receive my full analysis report via email
              </label>
            </div>
            
            {state.emailConsent && (
              <div>
                <input
                  type="email"
                  value={state.email}
                  onChange={(e) => dispatch({ type: ACTION_TYPES.SET_EMAIL, payload: e.target.value })}
                  placeholder="Enter your email address"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-200 focus:border-transparent"
                />
              </div>
            )}
          </div>
        </div>

        {/* Analysis Button */}
        <div className="mt-6">
          <button
            onClick={() => {
              if (!state.transcript.trim() && !state.file) {
                dispatch({
                  type: ACTION_TYPES.SHOW_MODAL,
                  payload: {
                    type: 'error',
                    title: 'No Content',
                    message: 'Please provide a transcript or upload a file before starting analysis.'
                  }
                });
                return;
              }
              
              if (state.emailConsent && !state.email.trim()) {
                dispatch({
                  type: ACTION_TYPES.SHOW_MODAL,
                  payload: {
                    type: 'error',
                    title: 'Email Required',
                    message: 'Please enter your email address to receive the full report.'
                  }
                });
                return;
              }
              
              // Start SHAPE analysis
              dispatch({ type: ACTION_TYPES.SET_ANALYSIS_STATE, payload: true });
              
              // Add analysis messages
              dispatch({
                type: ACTION_TYPES.ADD_MESSAGE,
                payload: { content: 'Starting SHAPE analysis...', sender: 'system' }
              });
              
              // Run the actual analysis
              setTimeout(() => {
                try {
                  const transcript = state.transcript.trim();
                  const result = analyzeSHAPE(transcript);
                  
                  dispatch({
                    type: ACTION_TYPES.ADD_MESSAGE,
                    payload: { content: `Analysis complete! SHAPE Score: ${result.scores.total}/100`, sender: 'system' }
                  });
                  
                  dispatch({ type: ACTION_TYPES.SET_RESULT, payload: result });
                  dispatch({ type: ACTION_TYPES.SET_ANALYSIS_STATE, payload: false });
                } catch (error) {
                  dispatch({
                    type: ACTION_TYPES.ADD_MESSAGE,
                    payload: { content: `Analysis error: ${error.message}`, sender: 'system' }
                  });
                  dispatch({ type: ACTION_TYPES.SET_ANALYSIS_STATE, payload: false });
                }
              }, 2000); // Simulate processing time
            }}
            disabled={state.isAnalyzing || (!state.transcript.trim() && !state.file)}
            className={`w-full py-3 px-6 rounded-lg font-semibold transition-all ${
              state.isAnalyzing || (!state.transcript.trim() && !state.file)
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-orange-500 hover:bg-orange-600 text-white shadow-lg hover:shadow-xl'
            }`}
          >
            {state.isAnalyzing ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Analyzing...
              </div>
            ) : (
              'Start Analysis'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// Analysis Panel Component
const AnalysisPanel = ({ state, dispatch }) => {
  return (
    <div className="w-1/2 bg-gray-50 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center mr-3">
            <Brain className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">AICS Analysis</h2>
        </div>
        <p className="text-gray-600">Real-time analysis of your conversation</p>
      </div>

      <div className="p-6 flex-1">
        {state.isAnalyzing ? (
          <div className="space-y-4">
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Analyzing Your Conversation</h3>
              <p className="text-gray-600">This may take a few moments...</p>
            </div>
            
            <div className="space-y-3">
              {state.analysisMessages.map((message) => (
                <div
                  key={message.id}
                  className={`p-3 rounded-lg ${
                    message.sender === 'system'
                      ? 'bg-blue-50 border border-blue-200'
                      : 'bg-white border border-gray-200'
                  }`}
                >
                  <div className="flex items-start">
                    <div className={`w-2 h-2 rounded-full mt-2 mr-3 ${
                      message.sender === 'system' ? 'bg-blue-500' : 'bg-gray-400'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700">{message.content}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : state.result ? (
          <div className="space-y-6">
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">SHAPE Analysis Complete!</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <span className="text-green-800 font-medium">Total SHAPE Score</span>
                  <span className="text-green-600 font-semibold">{state.result.scores?.total || 0}/100</span>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="text-xs text-blue-600 font-medium">S</div>
                    <div className="text-lg font-bold text-blue-800">{state.result.scores?.S?.score || 0}</div>
                    <div className="text-xs text-blue-500">{state.result.scores?.S?.hits || 0}/5</div>
                  </div>
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="text-xs text-green-600 font-medium">H</div>
                    <div className="text-lg font-bold text-green-800">{state.result.scores?.H?.score || 0}</div>
                    <div className="text-xs text-green-500">{state.result.scores?.H?.hits || 0}/5</div>
                  </div>
                  <div className="text-center p-2 bg-purple-50 rounded">
                    <div className="text-xs text-purple-600 font-medium">A</div>
                    <div className="text-lg font-bold text-purple-800">{state.result.scores?.A?.score || 0}</div>
                    <div className="text-xs text-purple-500">{state.result.scores?.A?.hits || 0}/5</div>
                  </div>
                  <div className="text-center p-2 bg-orange-50 rounded">
                    <div className="text-xs text-orange-600 font-medium">P</div>
                    <div className="text-lg font-bold text-orange-800">{state.result.scores?.P?.score || 0}</div>
                    <div className="text-xs text-orange-500">{state.result.scores?.P?.hits || 0}/5</div>
                  </div>
                  <div className="text-center p-2 bg-red-50 rounded">
                    <div className="text-xs text-red-600 font-medium">E</div>
                    <div className="text-lg font-bold text-red-800">{state.result.scores?.E?.score || 0}</div>
                    <div className="text-xs text-red-500">{state.result.scores?.E?.hits || 0}/5</div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-gray-800 font-medium">Conversation Stats</span>
                  <span className="text-gray-600 font-semibold">{state.result.stats?.turns || 0} turns, {state.result.stats?.userTurns || 0} user</span>
                </div>
              </div>
            </div>
            
            {!state.showFullReport && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-start">
                  <Lightbulb className="h-5 w-5 text-orange-600 mr-3 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="font-semibold text-orange-800 mb-2">Unlock Full Report</h4>
                    <p className="text-orange-700 text-sm mb-3">
                      Get detailed insights, recommendations, and actionable next steps for your conversation.
                    </p>
                    <button
                      onClick={() => dispatch({ type: ACTION_TYPES.UNLOCK_FULL_REPORT })}
                      className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      Unlock Full Report
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            {state.showFullReport && (
              <div className="bg-white rounded-lg p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Full Analysis Report</h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">SHAPE Insights</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      {state.result.insights?.map((insight, index) => (
                        <li key={index} className="flex items-start">
                          <Target className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                          <span className="font-medium text-blue-600">[{insight.domain}]</span> {insight.finding}
                        </li>
                      )) || (
                        <li className="text-gray-500 italic">No insights available</li>
                      )}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Actionable Recommendations</h4>
                    <ul className="space-y-2 text-sm text-gray-700">
                      {state.result.recommendations?.map((rec, index) => (
                        <li key={index} className="flex items-start">
                          <Compass className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                          {rec}
                        </li>
                      )) || (
                        <li className="text-gray-500 italic">No recommendations available</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                onClick={() => dispatch({ type: ACTION_TYPES.RESET_ALL })}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Start New Analysis
              </button>
              <button
                onClick={() => dispatch({ type: ACTION_TYPES.CLEAR_MESSAGES })}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg transition-colors"
              >
                Clear Messages
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <MessageSquare className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready to Analyze</h3>
            <p className="text-gray-600">Upload a file or paste your conversation to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const fileInputRef = useRef(null);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="flex h-screen">
        <InputPanel state={state} dispatch={dispatch} fileInputRef={fileInputRef} />
        <AnalysisPanel state={state} dispatch={dispatch} />
      </div>
      
      <Modal modal={state.modal} dispatch={dispatch} />
    </div>
  );
};

export default App;
