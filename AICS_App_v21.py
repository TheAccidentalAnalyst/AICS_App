import React, { useReducer, useRef, useEffect } from 'react';
import {
  BarChart3, Upload, CheckCircle, AlertCircle, FileText, MessageSquare,
  Brain, Eye, Edit3, Compass, Lightbulb, X, Target
} from 'lucide-react';

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
                    ? 'border
