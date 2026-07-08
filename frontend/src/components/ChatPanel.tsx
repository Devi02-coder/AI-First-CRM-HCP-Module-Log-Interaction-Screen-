import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import {
  addMessage, setLoading,
} from '../store/slices';
import {
  setActiveInteraction,
} from '../store/slices';
import {
  setToolLogs, clearToolLogs, addToast,
} from '../store/slices';
import { setTyping } from '../store/slices';
import { sendChatMessage } from '../services/api';
import {
  Loader2, CheckCircle2
} from 'lucide-react';

// ──────────────────────────────────────────────
// Renders a single message string with:
//   **bold** → <strong>
//   \n        → line breaks / bullet-aware
//   • item   → bullet rows
// ──────────────────────────────────────────────
const FormattedMessage: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split('\n');

  return (
    <span className="block">
      {lines.map((line, li) => {
        if (line.trim() === '') {
          return <span key={li} className="block h-1" />;
        }

        // Render inline bold segments
        const renderBold = (raw: string) => {
          const parts = raw.split(/\*\*([^*]+)\*\*/g);
          return parts.map((part, i) =>
            i % 2 === 1
              ? <strong key={i} className="font-semibold">{part}</strong>
              : <span key={i}>{part}</span>
          );
        };

        // Bullet line (• or - at start)
        if (line.trimStart().startsWith('•') || line.trimStart().startsWith('-')) {
          const content = line.replace(/^[\s•\-]+/, '');
          return (
            <span key={li} className="flex items-start gap-1.5 mt-0.5">
              <span className="mt-0.5 text-current opacity-60 flex-shrink-0">•</span>
              <span>{renderBold(content)}</span>
            </span>
          );
        }

        return (
          <span key={li} className="block">
            {renderBold(line)}
          </span>
        );
      })}
    </span>
  );
};

// ──────────────────────────────────────────────
// Main ChatPanel
// ──────────────────────────────────────────────
const ChatPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { messages, loading } = useAppSelector(s => s.chat);
  const { typing } = useAppSelector(s => s.ui);
  const { toolLogs } = useAppSelector(s => s.agent);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing, toolLogs]);

  // Connect WebSocket
  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'CRM_STATE_UPDATE') {
              if (data.interaction_data && Object.keys(data.interaction_data).length > 0) {
                dispatch(setActiveInteraction({
                  ...data.interaction_data,
                  products_discussed: data.interaction_data.products_discussed || [],
                  samples_distributed: data.interaction_data.samples_distributed || [],
                  materials_shared: data.interaction_data.materials_shared || [],
                }));
              }
              if (data.tool_logs && data.tool_logs.length > 0) {
                dispatch(setToolLogs(data.tool_logs));
              }
            }
          } catch { }
        };
        ws.onclose = () => { setTimeout(connect, 3000); };
        ws.onerror = () => { ws.close(); };
      } catch { }
    };
    connect();
  }, [dispatch]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput('');
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
  }, [input, loading, dispatch]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  // Detect if a message is the default instruction prompt
  const isInstructionMessage = (msg: string) =>
    msg.includes('Log interaction details here') || msg.includes("e.g.,");

  // Detect if it's a success/action assistant response
  const isActionResponse = (msg: string) =>
    msg.startsWith('✅') ||
    msg.startsWith('📋') ||
    msg.startsWith('📝') ||
    msg.startsWith('🎯') ||
    msg.startsWith('⚠️') ||
    msg.startsWith('✔️') ||
    msg.includes('logged successfully') ||
    msg.includes('updated successfully') ||
    msg.includes('interactions found') ||
    msg.includes('generated successfully') ||
    msg.includes('Suggested Follow-up') ||
    msg.includes('Record validated');

  return (
    <div className="flex flex-col h-full p-5 text-slate-700 bg-white">
      {/* Header */}
      <div className="pb-3 mb-4 border-b border-slate-100 flex flex-col justify-start">
        <div className="flex items-center gap-1.5">
          <span className="text-xl">🤖</span>
          <h2 className="text-base font-extrabold text-[#3b82f6]">AI Assistant</h2>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">Log interaction details here via chat</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 mb-4">

        {messages.map((msg, index) => {
          // ── Instruction / hint bubble (assistant, default message) ──
          if (msg.sender === 'assistant' && isInstructionMessage(msg.message)) {
            return (
              <div key={index} className="flex justify-start">
                <div className="p-3 bg-[#e0f2fe] border border-[#bae6fd] text-[#0369a1] rounded-lg text-xs max-w-[280px] leading-relaxed font-normal shadow-sm">
                  <FormattedMessage text={msg.message} />
                </div>
              </div>
            );
          }

          // ── User message ──
          if (msg.sender === 'user') {
            return (
              <div key={index} className="flex justify-end">
                <div className="p-3 bg-[#3b82f6] text-white rounded-lg rounded-br-none text-xs max-w-[280px] leading-relaxed shadow-sm font-normal">
                  <FormattedMessage text={msg.message} />
                </div>
              </div>
            );
          }

          // ── Assistant action response (green card) ──
          if (isActionResponse(msg.message)) {
            const isLoggedSuccess = msg.message.includes("Interaction logged successfully!");
            return (
              <div key={index} className="flex justify-start">
                <div className="p-3 bg-[#f0fdf4] border border-[#bbf7d0] text-[#166534] rounded-lg rounded-bl-none text-xs max-w-[280px] leading-relaxed shadow-sm font-normal">
                  {isLoggedSuccess ? msg.message : <FormattedMessage text={msg.message} />}
                </div>
              </div>
            );
          }

          // ── General assistant response (neutral card) ──
          const isLoggedSuccess = msg.message.includes("Interaction logged successfully!");
          return (
            <div key={index} className="flex justify-start">
              <div className="p-3 bg-[#f8fafc] border border-[#e2e8f0] text-[#334155] rounded-lg rounded-bl-none text-xs max-w-[280px] leading-relaxed shadow-sm font-normal">
                {isLoggedSuccess ? msg.message : <FormattedMessage text={msg.message} />}
              </div>
            </div>
          );
        })}

        {/* Tool execution logs (compact inline) */}
        {toolLogs.length > 0 && (
          <div className="p-2.5 bg-slate-50 border border-slate-200/80 rounded-lg space-y-1.5 max-w-[260px]">
            <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest">
              Tool Execution
            </span>
            {toolLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-1.5 text-[10px] text-slate-600 font-medium">
                <CheckCircle2 className="w-3 h-3 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>{log.step}: <span className="text-slate-500 font-normal">{log.status}</span></span>
              </div>
            ))}
          </div>
        )}

        {/* Typing indicator */}
        {typing && (
          <div className="flex justify-start items-center gap-1.5 text-slate-400 text-xs pl-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span className="text-[11px]">AI is processing...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="flex items-center">
        <input
          type="text"
          id="chat-input"
          className="flex-1 text-xs border border-slate-300 rounded-l-md px-3 py-2.5 outline-none focus:border-blue-400 bg-white placeholder-slate-400"
          placeholder="Describe interaction..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          id="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="flex items-center gap-1.5 px-4 py-2.5 bg-[#5f748d] hover:bg-[#4d6077] disabled:bg-slate-300 text-white rounded-r-md font-bold text-xs transition-colors"
        >
          {loading
            ? <Loader2 className="w-3 h-3 animate-spin" />
            : (
              <svg className="w-3 h-3 rotate-90 fill-current" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            )
          }
          Log
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
