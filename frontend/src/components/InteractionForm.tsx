import React from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { updateInteractionField } from '../store/slices';
import {
  Calendar, Clock, Mic, Search, Plus,
  Smile, Meh, Frown, Gift
} from 'lucide-react';

const InteractionForm: React.FC = () => {
  const dispatch = useAppDispatch();
  const { activeInteraction } = useAppSelector(s => s.interaction);
  const d = activeInteraction;

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
          <Mic className="absolute bottom-3 right-3 w-4 h-4 text-slate-400 cursor-pointer hover:text-slate-600" />
        </div>
      </div>

      {/* Voice Note Button */}
      <div className="mb-5">
        <button
          type="button"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#eaeef4] hover:bg-[#dee4ec] text-[11px] font-semibold text-slate-700 rounded-md border border-slate-300/40 transition-colors"
        >
          <svg className="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z" />
          </svg>
          Summarize from Voice Note (Requires Consent)
        </button>
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
