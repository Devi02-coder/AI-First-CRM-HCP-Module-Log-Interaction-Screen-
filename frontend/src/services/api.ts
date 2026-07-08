import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

export interface ChatRequest { message: string; }
export interface ChatResponse {
  response: string;
  interaction_data: Record<string, any> | null;
  current_tool: string | null;
  validation_status: string | null;
  tool_execution_logs: Array<{ step: string; status: string }>;
}

export const sendChatMessage = async (message: string): Promise<ChatResponse> => {
  const { data } = await api.post<ChatResponse>('/api/chat', { message });
  return data;
};

export const getInteractions = async () => {
  const { data } = await api.get('/api/interactions');
  return data;
};

export const getInteraction = async (id: number) => {
  const { data } = await api.get(`/api/interactions/${id}`);
  return data;
};

export const getChatHistory = async () => {
  const { data } = await api.get('/api/chat/history');
  return data;
};

export const getToolLogs = async () => {
  const { data } = await api.get('/api/tool-logs');
  return data;
};

export const getAuditLogs = async () => {
  const { data } = await api.get('/api/audit-logs');
  return data;
};

export const getHCPHistory = async (id: number) => {
  const { data } = await api.get(`/api/hcp/${id}/history`);
  return data;
};

export default api;
