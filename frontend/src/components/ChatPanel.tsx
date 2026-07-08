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
  Bot, Loader2, Send, CheckCircle2
} from 'lucide-react';

const ChatPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { messages, loading } = useAppSelector(s => s.chat);
  const { typing } = useAppSelector(s => s.ui);
  const { toolLogs } = useAppSelector(s => s.agent);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing, toolLogs]);

  // Connect WebSocket
  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onopen = () => { setWsConnected(true); };
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
          } catch {}
        };
        ws.onclose = () => { setWsConnected(false); setTimeout(connect, 3000); };
        ws.onerror = () => { ws.close(); };
      } catch {}
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

    } catch (err) {
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

  const formatMessageText = (text: string) => {
    const parts = text.split(/\*\*([^*]+)\*\*/g);
    return parts.map((part, i) => {
      if (i % 2 === 1) {
        return <strong key={i} className="font-bold">{part}</strong>;
      }
      return part;
    });
  };

  return (
    <div className="flex flex-col h-[680px] p-5 text-slate-700 bg-white">
      {/* Header */}
      <div className="pb-3 mb-4 border-b border-slate-100 flex flex-col justify-start">
        <div className="flex items-center gap-1.5">
          <span className="text-xl">🤖</span>
          <h2 className="text-base font-extrabold text-[#3b82f6]">AI Assistant</h2>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">Log Interaction details here via chat</p>
      </div>

      {/* Message and scroll box */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {/* User/Agent Dialogues */}
        {messages.filter(m => m.sender === 'user' || m.message !== '').map((msg, index) => {
          const isInstruction = msg.sender === 'assistant' && msg.message.includes('Log interaction details');
          
          if (isInstruction) {
            return (
              <div key={index} className="flex justify-start">
                <div className="p-3 bg-[#e0f2fe] border border-[#bae6fd] text-[#0369a1] rounded-lg text-xs max-w-sm leading-relaxed font-normal shadow-sm">
                  {msg.message}
                </div>
              </div>
            );
          }

          if (msg.sender === 'user') {
            return (
              <div key={index} className="flex justify-start">
                <div className="p-3 bg-[#f1f5f9] border-l-[3px] border-[#3b82f6] text-[#1e293b] rounded-r-lg rounded-bl-lg text-xs max-w-sm leading-relaxed shadow-sm font-normal">
                  {msg.message}
                </div>
              </div>
            );
          }

          // Assistant Log / Response message (Green Card)
          let displayMsg = msg.message;
          if (!displayMsg.startsWith('✅') && !displayMsg.startsWith('🤖')) {
            displayMsg = '✅ ' + displayMsg;
          }

          return (
            <div key={index} className="flex justify-start">
              <div className="p-3 bg-[#f0fdf4] border border-[#bbf7d0] text-[#166534] rounded-lg text-xs max-w-sm leading-relaxed shadow-sm font-normal">
                {formatMessageText(displayMsg)}
              </div>
            </div>
          );
        })}

        {/* Tool logs inline inside chat area */}
        {toolLogs.length > 0 && (
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg space-y-2 max-w-xs">
            <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest">
              Execution Logs
            </span>
            {toolLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-1.5 text-[11px] text-slate-600 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>{log.step}: {log.status}</span>
              </div>
            ))}
          </div>
        )}

        {typing && (
          <div className="flex justify-start items-center gap-1 text-slate-400 text-xs pl-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>AI is updating form...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input container at the bottom matching the master screenshot */}
      <div className="flex items-center">
        <input
          type="text"
          className="flex-1 text-xs border border-slate-300 rounded-l-md px-3 py-2.5 outline-none focus:border-slate-400 bg-white placeholder-slate-400"
          placeholder="Describe interaction..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="flex items-center gap-1.5 px-4 py-2.5 bg-[#5f748d] hover:bg-[#4d6077] disabled:bg-slate-300 text-white rounded-r-md font-bold text-xs transition-colors"
        >
          <svg className="w-3 h-3 rotate-90 fill-current" viewBox="0 0 20 20">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
          Log
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
