import React from 'react';
import { X, CheckCircle2, AlertTriangle, Info, AlertCircle } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../store';
import { removeToast } from '../store/slices';

const ICONS = {
  success: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
  error: <AlertCircle className="w-4 h-4 text-red-500" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-500" />,
  info: <Info className="w-4 h-4 text-blue-500" />,
};

const BG = {
  success: 'bg-white border-emerald-200',
  error: 'bg-white border-red-200',
  warning: 'bg-white border-amber-200',
  info: 'bg-white border-blue-200',
};

const ToastContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { toasts } = useAppSelector(s => s.ui);

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 p-3 rounded-xl border shadow-lg pointer-events-auto
            animate-[slideIn_0.3s_ease] ${BG[toast.type]}`}
        >
          <span className="flex-shrink-0 mt-0.5">{ICONS[toast.type]}</span>
          <p className="text-sm text-slate-700 flex-1 leading-snug">{toast.message}</p>
          <button
            onClick={() => dispatch(removeToast(toast.id))}
            className="flex-shrink-0 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default ToastContainer;
