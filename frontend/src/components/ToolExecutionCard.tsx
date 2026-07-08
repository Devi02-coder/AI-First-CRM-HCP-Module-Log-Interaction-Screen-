import React from 'react';
import { useAppSelector } from '../store';
import {
  CheckCircle2, Loader2, Zap, Database,
  Search, Edit3, BarChart3, Shield, ChevronRight
} from 'lucide-react';

const TOOL_ICONS: Record<string, React.ReactNode> = {
  'User Input Node': <Zap className="w-3 h-3" />,
  'Intent Classification Node': <Search className="w-3 h-3" />,
  'Tool Execution Node': <Zap className="w-3 h-3" />,
  'Log Interaction Tool': <Database className="w-3 h-3" />,
  'Entity Extraction': <Search className="w-3 h-3" />,
  'Edit Applied': <Edit3 className="w-3 h-3" />,
  'Edit Interaction Tool': <Edit3 className="w-3 h-3" />,
  'Interaction Summary Tool': <BarChart3 className="w-3 h-3" />,
  'HCP History Retrieval': <Search className="w-3 h-3" />,
  'Next Best Action Tool': <ChevronRight className="w-3 h-3" />,
  'Validation Node': <Shield className="w-3 h-3" />,
  'Database Persistence Node': <Database className="w-3 h-3" />,
  'Response Generation Node': <Zap className="w-3 h-3" />,
  'State Update Node': <Zap className="w-3 h-3" />,
};

const ToolExecutionCard: React.FC = () => {
  const { toolLogs } = useAppSelector(s => s.agent);
  const { loading } = useAppSelector(s => s.chat);

  if (toolLogs.length === 0 && !loading) return null;

  return (
    <div className="mx-3 mb-2 bg-slate-900 rounded-xl overflow-hidden border border-slate-800 shadow-lg">
      {/* Terminal-style header */}
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800 border-b border-slate-700">
        <div className="flex gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
        </div>
        <span className="text-[10px] font-mono text-slate-400 tracking-widest uppercase ml-1">
          LangGraph Agent Execution
        </span>
        {loading && <Loader2 className="w-3 h-3 text-indigo-400 animate-spin ml-auto" />}
      </div>

      {/* Log entries */}
      <div className="p-3 space-y-1.5 max-h-48 overflow-y-auto">
        {toolLogs.map((log, idx) => {
          const icon = TOOL_ICONS[log.step] || <Zap className="w-3 h-3" />;
          const isLast = idx === toolLogs.length - 1;
          return (
            <div key={idx} className="flex items-start gap-2">
              {/* Timeline connector */}
              <div className="flex flex-col items-center flex-shrink-0 mt-0.5">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                  isLast && loading
                    ? 'bg-indigo-500/20 border border-indigo-500/40'
                    : 'bg-emerald-500/20 border border-emerald-500/40'
                }`}>
                  {isLast && loading
                    ? <Loader2 className="w-2.5 h-2.5 text-indigo-400 animate-spin" />
                    : <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />}
                </div>
                {idx < toolLogs.length - 1 && <div className="w-px h-3 bg-slate-700 my-0.5" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-500">{icon}</span>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{log.step}</span>
                </div>
                <p className="text-xs text-slate-300 font-mono mt-0.5 leading-relaxed truncate">{log.status}</p>
              </div>
            </div>
          );
        })}
        {loading && toolLogs.length === 0 && (
          <div className="flex items-center gap-2 py-1">
            <Loader2 className="w-3 h-3 text-indigo-400 animate-spin" />
            <span className="text-xs text-slate-400 font-mono">Initializing agent workflow...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolExecutionCard;
