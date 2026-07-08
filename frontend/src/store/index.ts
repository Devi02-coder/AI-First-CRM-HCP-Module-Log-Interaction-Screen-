import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import { authReducer, chatReducer, interactionReducer, agentReducer, uiReducer } from './slices';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    interaction: interactionReducer,
    agent: agentReducer,
    ui: uiReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
