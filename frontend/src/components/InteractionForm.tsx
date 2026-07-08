import React, { useState, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import {
  updateInteractionField,
  setActiveInteraction,
  addMessage,
  setLoading,
  setTyping,
  setToolLogs,
  clearToolLogs,
  addToast
} from '../store/slices';
import { sendChatMessage, transcribeAudio } from '../services/api';
import {
  Calendar, Clock, Mic, Search, Plus,
  Smile, Meh, Frown, Gift
} from 'lucide-react';

const InteractionForm: React.FC = () => {
  const dispatch = useAppDispatch();
  const { activeInteraction } = useAppSelector(s => s.interaction);
  const d = activeInteraction;

  const [isRecordingMic, setIsRecordingMic] = useState(false);
  const [isRecordingVoiceNote, setIsRecordingVoiceNote] = useState(false);
  const [micStatus, setMicStatus] = useState<'ready' | 'recording' | 'processing' | 'complete'>('ready');
  const [voiceStatus, setVoiceStatus] = useState<'ready' | 'recording' | 'processing' | 'complete'>('ready');
  const recognitionMicRef = useRef<any>(null);
  const recognitionVoiceNoteRef = useRef<any>(null);
  const voiceTranscriptRef = useRef<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadFallbackTargetRef = useRef<'mic' | 'voice_note' | null>(null);

  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  const requestMicPermission = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('browser-unsupported');
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (err: any) {
      console.error('Microphone permission check failed:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        throw new Error('permission-denied');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        throw new Error('no-microphone');
      } else if (err.message === 'browser-unsupported') {
        throw new Error('browser-unsupported');
      } else {
        throw new Error('permission-blocked');
      }
    }
  };

  const handleMicError = (errorType: string, target: 'mic' | 'voice_note') => {
    let message = '';
    switch (errorType) {
      case 'permission-denied':
        message = 'Microphone access is required for voice input. Please allow microphone permissions in your browser settings.';
        break;
      case 'permission-blocked':
        message = 'Microphone permission blocked or unavailable. Please review browser settings.';
        break;
      case 'no-microphone':
        message = 'No microphone found on your device. Please connect a microphone.';
        break;
      case 'browser-unsupported':
        message = 'Speech recognition or media device access is not supported by your browser.';
        break;
      default:
        message = 'Microphone permission denied';
    }
    
    dispatch(addToast({
      id: Date.now().toString(),
      type: 'error',
      message: message,
    }));
    
    uploadFallbackTargetRef.current = target;
    triggerAudioUploadFallback();
  };

  const triggerAudioUploadFallback = () => {
    const confirmUpload = window.confirm(
      'Microphone access is blocked. Would you like to upload an audio file (mp3, wav, m4a, webm) to transcribe instead?'
    );
    if (confirmUpload && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleAudioFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    e.target.value = '';
    const target = uploadFallbackTargetRef.current;
    if (target === 'mic') {
      setMicStatus('processing');
    } else {
      setVoiceStatus('processing');
    }

    try {
      const resp = await transcribeAudio(file);
      const text = resp.text;
      
      if (target === 'mic') {
        const currentText = d.key_discussion_points ? d.key_discussion_points + ' ' : '';
        handleInputChange('key_discussion_points', currentText + text);
        setMicStatus('complete');
        setTimeout(() => setMicStatus('ready'), 3000);
      } else {
        setVoiceStatus('complete');
        setTimeout(() => setVoiceStatus('ready'), 3000);
        submitVoiceTranscript(text);
      }
    } catch (err) {
      console.error('Upload transcription failed:', err);
      dispatch(addToast({
        id: Date.now().toString(),
        type: 'error',
        message: 'Audio transcription failed. Please check backend connection.',
      }));
      if (target === 'mic') {
        setMicStatus('ready');
      } else {
        setVoiceStatus('ready');
      }
    }
  };

  const toggleMicRecording = async () => {
    if (isRecordingMic) {
      if (recognitionMicRef.current) {
        recognitionMicRef.current.stop();
      }
      setIsRecordingMic(false);
      setMicStatus('ready');
    } else {
      try {
        setMicStatus('processing');
        await requestMicPermission();
        
        if (!SpeechRecognition) {
          throw new Error('browser-unsupported');
        }
        
        const rec = new SpeechRecognition();
        rec.continuous = true;
        rec.interimResults = false;
        rec.lang = 'en-US';
        
        rec.onstart = () => {
          setIsRecordingMic(true);
          setMicStatus('recording');
        };
        
        rec.onresult = (event: any) => {
          const resultText = event.results[event.results.length - 1][0].transcript;
          const currentText = d.key_discussion_points ? d.key_discussion_points + ' ' : '';
          handleInputChange('key_discussion_points', currentText + resultText);
        };
        
        rec.onerror = (event: any) => {
          console.error(event.error);
          setIsRecordingMic(false);
          setMicStatus('ready');
          handleMicError(event.error === 'not-allowed' ? 'permission-denied' : event.error, 'mic');
        };
        
        rec.onend = () => {
          setIsRecordingMic(false);
          setMicStatus('complete');
          setTimeout(() => setMicStatus('ready'), 2000);
        };
        
        recognitionMicRef.current = rec;
        rec.start();
      } catch (err: any) {
        setMicStatus('ready');
        handleMicError(err.message, 'mic');
      }
    }
  };

  const submitVoiceTranscript = async (text: string) => {
    dispatch(clearToolLogs());
    dispatch(addMessage({ sender: 'user', message: text, timestamp: new Date().toISOString() }));
    dispatch(setLoading(true));
    dispatch(setTyping(true));
    
    try {
      const resp = await sendChatMessage(text);
      if (resp.tool_execution_logs?.length) {
        dispatch(setToolLogs(resp.tool_execution_logs));
      }
      if (resp.interaction_data && Object.keys(resp.interaction_data).length > 0) {
        const d = resp.interaction_data;
        dispatch(setActiveInteraction({
          id: d.id,
          hcp_name: d.hcp_name || '',
          specialty: d.specialty || '',
          hospital_clinic: d.hospital_clinic || '',
          tier: d.tier || 'B',
          territory: d.territory || '',
          interaction_date: d.interaction_date || '',
          interaction_time: d.interaction_time || '19:36',
          interaction_type: d.interaction_type || 'Meeting',
          attendees: d.attendees || '',
          visit_objective: d.visit_objective || '',
          products_discussed: d.products_discussed || [],
          samples_distributed: d.samples_distributed || [],
          materials_shared: d.materials_shared || [],
          key_discussion_points: d.key_discussion_points || '',
          objections_raised: d.objections_raised || '',
          sentiment: d.sentiment || 'Neutral',
          outcome: d.outcome || '',
          follow_up_required: d.follow_up_required || false,
          follow_up_date: d.follow_up_date || '',
          next_best_action: d.next_best_action || '',
          interaction_summary: d.interaction_summary || '',
          validation_status: d.validation_status || 'Pending',
          last_updated: new Date().toISOString(),
        }));
        
        dispatch(addToast({
          id: Date.now().toString(),
          type: resp.validation_status === 'Valid' ? 'success' : 'info',
          message: resp.validation_status === 'Valid'
            ? 'CRM record saved and validated.'
            : 'Record saved with validation alerts.',
        }));
      }
      dispatch(addMessage({
        sender: 'assistant',
        message: resp.response,
        timestamp: new Date().toISOString()
      }));
    } catch {
      dispatch(addMessage({
        sender: 'assistant',
        message: 'Could not communicate with the CRM agent. Please check if the FastAPI backend is running.',
        timestamp: new Date().toISOString()
      }));
    } finally {
      dispatch(setLoading(false));
      dispatch(setTyping(false));
    }
  };

  const startVoiceNoteRecording = async () => {
    try {
      const consent = window.confirm('Do you consent to enable microphone access to record and transcribe your voice note?');
      if (!consent) return;

      setVoiceStatus('processing');
      await requestMicPermission();
      
      if (!SpeechRecognition) {
        throw new Error('browser-unsupported');
      }

      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = false;
      rec.lang = 'en-US';
      voiceTranscriptRef.current = '';

      rec.onstart = () => {
        setIsRecordingVoiceNote(true);
        setVoiceStatus('recording');
      };
      rec.onresult = (event: any) => {
        const resultText = event.results[event.results.length - 1][0].transcript;
        voiceTranscriptRef.current += (voiceTranscriptRef.current ? ' ' : '') + resultText;
      };
      rec.onerror = (event: any) => {
        console.error(event.error);
        setIsRecordingVoiceNote(false);
        setVoiceStatus('ready');
        handleMicError(event.error === 'not-allowed' ? 'permission-denied' : event.error, 'voice_note');
      };
      rec.onend = async () => {
        setIsRecordingVoiceNote(false);
        setVoiceStatus('complete');
        setTimeout(() => setVoiceStatus('ready'), 2000);
        
        const text = voiceTranscriptRef.current.trim();
        if (!text) {
          dispatch(addToast({
            id: Date.now().toString(),
            type: 'info',
            message: 'No speech detected.',
          }));
          return;
        }
        submitVoiceTranscript(text);
      };

      recognitionVoiceNoteRef.current = rec;
      rec.start();
    } catch (err: any) {
      setVoiceStatus('ready');
      handleMicError(err.message, 'voice_note');
    }
  };

  const stopVoiceNoteRecording = () => {
    if (recognitionVoiceNoteRef.current) {
      recognitionVoiceNoteRef.current.stop();
    }
  };

  const handleInputChange = (field: string, value: any) => {
    dispatch(updateInteractionField({ [field]: value }));
  };

  const addSuggestedFollowUp = (text: string) => {
    const currentActions = d.next_best_action ? d.next_best_action + '\n' : '';
    handleInputChange('next_best_action', currentActions + '- ' + text);
  };

  return (
    <div className="p-6 text-slate-700">
      {/* Title */}
      <h2 className="text-base font-bold text-slate-800 border-b border-slate-100 pb-3 mb-5">
        Interaction Details
      </h2>

      {/* Row 1: HCP Name & Interaction Type */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">
            HCP Name
          </label>
          <input
            type="text"
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 outline-none focus:border-slate-400"
            placeholder="Search or select HCP..."
            value={d.hcp_name || ''}
            onChange={(e) => handleInputChange('hcp_name', e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">
            Interaction Type
          </label>
          <div className="relative">
            <select
              className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 outline-none appearance-none focus:border-slate-400 bg-white"
              value={d.interaction_type || 'Meeting'}
              onChange={(e) => handleInputChange('interaction_type', e.target.value)}
            >
              <option value="Meeting">Meeting</option>
              <option value="Call">Call</option>
              <option value="Email">Email</option>
              <option value="Video Call">Video Call</option>
            </select>
            <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-slate-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Date & Time */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">
            Date
          </label>
          <div className="relative flex items-center">
            <input
              type="text"
              className="w-full text-sm border border-slate-300 rounded-md pl-3 pr-10 py-2 outline-none focus:border-slate-400"
              placeholder="DD-MM-YYYY"
              value={d.interaction_date || ''}
              onChange={(e) => handleInputChange('interaction_date', e.target.value)}
            />
            <Calendar className="absolute right-3 w-4 h-4 text-slate-400" />
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">
            Time
          </label>
          <div className="relative flex items-center">
            <input
              type="text"
              className="w-full text-sm border border-slate-300 rounded-md pl-3 pr-10 py-2 outline-none focus:border-slate-400"
              placeholder="HH:MM"
              value={d.interaction_time || ''}
              onChange={(e) => handleInputChange('interaction_time', e.target.value)}
            />
            <Clock className="absolute right-3 w-4 h-4 text-slate-400" />
          </div>
        </div>
      </div>

      {/* Row 3: Attendees */}
      <div className="mb-4">
        <label className="block text-xs font-semibold text-slate-500 mb-1">
          Attendees
        </label>
        <input
          type="text"
          className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 outline-none focus:border-slate-400"
          placeholder="Enter names or search..."
          value={d.attendees || ''}
          onChange={(e) => handleInputChange('attendees', e.target.value)}
        />
      </div>

      {/* Row 4: Topics Discussed */}
      <div className="mb-3">
        <label className="block text-xs font-semibold text-slate-500 mb-1">
          Topics Discussed
        </label>
        <div className="relative">
          <textarea
            className="w-full text-sm border border-slate-300 rounded-md pl-3 pr-10 py-2 outline-none focus:border-slate-400 min-h-[90px]"
            placeholder="Enter key discussion points..."
            value={d.key_discussion_points || ''}
            onChange={(e) => handleInputChange('key_discussion_points', e.target.value)}
          />
          <Mic
            onClick={toggleMicRecording}
            title={micStatus === 'ready' ? '🎤 Click to record' : micStatus === 'recording' ? '🔴 Recording — click to stop' : micStatus === 'processing' ? '⏳ Checking permission…' : '✅ Done'}
            className={`absolute bottom-3 right-3 w-4 h-4 cursor-pointer transition-colors ${
              micStatus === 'recording' ? 'text-red-500 animate-pulse' :
              micStatus === 'processing' ? 'text-amber-400 animate-bounce' :
              micStatus === 'complete' ? 'text-emerald-500' : 'text-slate-400 hover:text-slate-600'
            }`}
          />
        </div>
        {micStatus !== 'ready' && (
          <p className={`text-[10px] mt-1 font-medium ${
            micStatus === 'recording' ? 'text-red-500' :
            micStatus === 'processing' ? 'text-amber-500' : 'text-emerald-600'
          }`}>
            {micStatus === 'recording' ? '🔴 Recording…' : micStatus === 'processing' ? '⏳ Checking microphone permission…' : '✅ Done'}
          </p>
        )}
      </div>

      {/* Voice Note Button + Status */}
      <div className="mb-5">
        <button
          type="button"
          onClick={isRecordingVoiceNote ? stopVoiceNoteRecording : startVoiceNoteRecording}
          disabled={voiceStatus === 'processing'}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border transition-colors text-[11px] font-semibold ${
            isRecordingVoiceNote
              ? 'bg-red-500 hover:bg-red-600 text-white border-red-500 animate-pulse'
              : voiceStatus === 'processing'
              ? 'bg-amber-50 text-amber-600 border-amber-300 cursor-not-allowed'
              : voiceStatus === 'complete'
              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
              : 'bg-[#eaeef4] hover:bg-[#dee4ec] text-slate-700 border-slate-300/40'
          }`}
        >
          {isRecordingVoiceNote ? (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-white animate-ping" />
              🔴 Recording… Click to Stop
            </span>
          ) : voiceStatus === 'processing' ? (
            <span>⏳ Checking microphone permission…</span>
          ) : voiceStatus === 'complete' ? (
            <span>✅ Voice note processed</span>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
              </svg>
              🎤 Summarize from Voice Note (Requires Consent)
            </>
          )}
        </button>

        {/* Hidden audio file input for Whisper fallback */}
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/mp3,audio/mpeg,audio/wav,audio/x-wav,audio/m4a,audio/mp4,audio/webm,.mp3,.wav,.m4a,.webm"
          className="hidden"
          onChange={handleAudioFileUpload}
        />
      </div>

      {/* Section: Materials Shared / Samples Distributed */}
      <div className="mb-5">
        <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
          Materials Shared / Samples Distributed
        </span>
        
        {/* Materials Box */}
        <div className="border border-slate-200 rounded-md p-3 mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-slate-800">Materials Shared</span>
            <button className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-slate-600 border border-slate-300 rounded hover:bg-slate-50">
              <Search className="w-3 h-3" /> Search/Add
            </button>
          </div>
          <div className="text-xs text-slate-400 italic">
            {d.materials_shared && d.materials_shared.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 mt-2 not-italic">
                {d.materials_shared.map((m, i) => (
                  <span key={i} className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-700 font-medium">
                    {m}
                  </span>
                ))}
              </div>
            ) : (
              "No materials added."
            )}
          </div>
        </div>

        {/* Samples Box */}
        <div className="border border-slate-200 rounded-md p-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-slate-800">Samples Distributed</span>
            <button className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-slate-600 border border-slate-300 rounded hover:bg-slate-50">
              <Gift className="w-3 h-3" /> Add Sample
            </button>
          </div>
          <div className="text-xs text-slate-400 italic">
            {d.samples_distributed && d.samples_distributed.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 mt-2 not-italic">
                {d.samples_distributed.map((s, i) => (
                  <span key={i} className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-700 font-medium">
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              "No samples added."
            )}
          </div>
        </div>
      </div>

      {/* Section: Observed/Inferred HCP Sentiment */}
      <div className="mb-5">
        <label className="block text-xs font-semibold text-slate-500 mb-2">
          Observed/Inferred HCP Sentiment
        </label>
        <div className="flex gap-6 items-center text-sm font-medium">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="radio"
              name="sentiment"
              value="Positive"
              checked={d.sentiment === 'Positive'}
              onChange={() => handleInputChange('sentiment', 'Positive')}
              className="accent-slate-700"
            />
            <Smile className="w-4 h-4 text-emerald-500" />
            Positive
          </label>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="radio"
              name="sentiment"
              value="Neutral"
              checked={d.sentiment === 'Neutral'}
              onChange={() => handleInputChange('sentiment', 'Neutral')}
              className="accent-slate-700"
            />
            <Meh className="w-4 h-4 text-amber-500" />
            Neutral
          </label>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="radio"
              name="sentiment"
              value="Negative"
              checked={d.sentiment === 'Negative'}
              onChange={() => handleInputChange('sentiment', 'Negative')}
              className="accent-slate-700"
            />
            <Frown className="w-4 h-4 text-red-500" />
            Negative
          </label>
        </div>
      </div>

      {/* Outcomes */}
      <div className="mb-4">
        <label className="block text-xs font-semibold text-slate-500 mb-1">
          Outcomes
        </label>
        <textarea
          className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 outline-none focus:border-slate-400 min-h-[70px]"
          placeholder="Key outcomes or agreements..."
          value={d.outcome || ''}
          onChange={(e) => handleInputChange('outcome', e.target.value)}
        />
      </div>

      {/* Follow-up Actions */}
      <div className="mb-4">
        <label className="block text-xs font-semibold text-slate-500 mb-1">
          Follow-up Actions
        </label>
        <textarea
          className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 outline-none focus:border-slate-400 min-h-[70px]"
          placeholder="Enter next steps or tasks..."
          value={d.next_best_action || ''}
          onChange={(e) => handleInputChange('next_best_action', e.target.value)}
        />
      </div>

      {/* AI Suggested Follow-ups */}
      <div className="mt-4 pt-1 border-t border-slate-100">
        <span className="block text-xs font-bold text-slate-800 mb-1.5">
          AI Suggested Follow-ups:
        </span>
        <ul className="text-xs text-blue-600 font-medium space-y-1.5">
          <li>
            <button
              onClick={() => addSuggestedFollowUp('Schedule follow-up meeting in 2 weeks')}
              className="hover:underline text-left text-blue-600 block"
            >
              + Schedule follow-up meeting in 2 weeks
            </button>
          </li>
          <li>
            <button
              onClick={() => addSuggestedFollowUp('Send OncoBoost Phase III PDF')}
              className="hover:underline text-left text-blue-600 block"
            >
              + Send OncoBoost Phase III PDF
            </button>
          </li>
          <li>
            <button
              onClick={() => addSuggestedFollowUp('Add Dr. Sharma to advisory board invite list')}
              className="hover:underline text-left text-blue-600 block"
            >
              + Add Dr. Sharma to advisory board invite list
            </button>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default InteractionForm;
