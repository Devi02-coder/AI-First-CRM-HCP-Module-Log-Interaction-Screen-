import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

// Auth Slice State
export interface UserState {
  username: string;
  role: string;
  email: string;
}
interface AuthSliceState {
  user: UserState | null;
}
const initialAuthState: AuthSliceState = {
  user: {
    username: 'rep_muthu',
    role: 'Medical Representative',
    email: 'muthu@pharmaco.com'
  }
};

export const authSlice = createSlice({
  name: 'auth',
  initialState: initialAuthState,
  reducers: {
    setUser: (state, action: PayloadAction<UserState | null>) => {
      state.user = action.payload;
    }
  }
});

// Chat Slice State
export interface ChatMessage {
  id?: number;
  sender: 'user' | 'assistant';
  message: string;
  timestamp?: string;
}
interface ChatSliceState {
  messages: ChatMessage[];
  loading: boolean;
}
const initialChatState: ChatSliceState = {
  messages: [
    {
      sender: 'assistant',
      message: 'Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.',
      timestamp: new Date().toISOString()
    }
  ],
  loading: false
};

export const chatSlice = createSlice({
  name: 'chat',
  initialState: initialChatState,
  reducers: {
    setMessages: (state, action: PayloadAction<ChatMessage[]>) => {
      state.messages = action.payload;
    },
    addMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload);
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    }
  }
});

// Interaction Form State
export interface InteractionData {
  id?: number;
  hcp_name: string;
  specialty: string;
  hospital_clinic: string;
  tier: string;
  territory: string;
  interaction_date: string;
  interaction_time?: string;
  interaction_type: string;
  attendees?: string;
  visit_objective: string;
  products_discussed: string[];
  samples_distributed: string[];
  materials_shared: string[];
  key_discussion_points: string;
  objections_raised: string;
  sentiment: string;
  outcome: string;
  follow_up_required: boolean;
  follow_up_date: string;
  next_best_action: string;
  interaction_summary: string;
  validation_status: string;
  last_updated?: string;
}
export interface ValidationIssue {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}
export interface ValidationReport {
  is_valid: boolean;
  validation_status: string;
  issues: ValidationIssue[];
}
interface InteractionSliceState {
  activeInteraction: InteractionData;
  history: InteractionData[];
  validationReport: ValidationReport;
}
const initialInteractionState: InteractionSliceState = {
  activeInteraction: {
    hcp_name: '',
    specialty: '',
    hospital_clinic: '',
    tier: 'B',
    territory: '',
    interaction_date: new Date().toISOString().split('T')[0],
    interaction_time: '19:36',
    interaction_type: 'Meeting',
    attendees: '',
    visit_objective: 'Product Detailing',
    products_discussed: [],
    samples_distributed: [],
    materials_shared: [],
    key_discussion_points: '',
    objections_raised: '',
    sentiment: 'Neutral',
    outcome: '',
    follow_up_required: false,
    follow_up_date: '',
    next_best_action: '',
    interaction_summary: '',
    validation_status: 'Pending'
  },
  history: [],
  validationReport: {
    is_valid: true,
    validation_status: 'Pending',
    issues: []
  }
};

export const interactionSlice = createSlice({
  name: 'interaction',
  initialState: initialInteractionState,
  reducers: {
    setActiveInteraction: (state, action: PayloadAction<InteractionData>) => {
      state.activeInteraction = action.payload;
    },
    updateInteractionField: (state, action: PayloadAction<Partial<InteractionData>>) => {
      state.activeInteraction = { ...state.activeInteraction, ...action.payload };
    },
    setHistory: (state, action: PayloadAction<InteractionData[]>) => {
      state.history = action.payload;
    },
    setValidationReport: (state, action: PayloadAction<ValidationReport>) => {
      state.validationReport = action.payload;
    },
    clearActiveInteraction: (state) => {
      state.activeInteraction = initialInteractionState.activeInteraction;
    }
  }
});

// Agent Slice State (Tool Logs and Timeline)
export interface ToolLogEntry {
  step: string;
  status: string;
  timestamp?: string;
}
interface AgentSliceState {
  toolLogs: ToolLogEntry[];
  auditLogs: any[];
}
const initialAgentState: AgentSliceState = {
  toolLogs: [],
  auditLogs: []
};

export const agentSlice = createSlice({
  name: 'agent',
  initialState: initialAgentState,
  reducers: {
    setToolLogs: (state, action: PayloadAction<ToolLogEntry[]>) => {
      state.toolLogs = action.payload;
    },
    addToolLog: (state, action: PayloadAction<ToolLogEntry>) => {
      state.toolLogs.push(action.payload);
    },
    clearToolLogs: (state) => {
      state.toolLogs = [];
    },
    setAuditLogs: (state, action: PayloadAction<any[]>) => {
      state.auditLogs = action.payload;
    }
  }
});

// UI Slice State
export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}
interface UISliceState {
  typing: boolean;
  toasts: ToastMessage[];
  activeSidebarTab: 'form' | 'timeline' | 'audit';
}
const initialUIState: UISliceState = {
  typing: false,
  toasts: [],
  activeSidebarTab: 'form'
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState: initialUIState,
  reducers: {
    setTyping: (state, action: PayloadAction<boolean>) => {
      state.typing = action.payload;
    },
    addToast: (state, action: PayloadAction<ToastMessage>) => {
      state.toasts.push(action.payload);
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(t => t.id !== action.payload);
    },
    setActiveSidebarTab: (state, action: PayloadAction<'form' | 'timeline' | 'audit'>) => {
      state.activeSidebarTab = action.payload;
    }
  }
});

export const { setUser } = authSlice.actions;
export const { setMessages, addMessage, setLoading } = chatSlice.actions;
export const { setActiveInteraction, updateInteractionField, setHistory, setValidationReport, clearActiveInteraction } = interactionSlice.actions;
export const { setToolLogs, addToolLog, clearToolLogs, setAuditLogs } = agentSlice.actions;
export const { setTyping, addToast, removeToast, setActiveSidebarTab } = uiSlice.actions;
export const authReducer = authSlice.reducer;
export const chatReducer = chatSlice.reducer;
export const interactionReducer = interactionSlice.reducer;
export const agentReducer = agentSlice.reducer;
export const uiReducer = uiSlice.reducer;
