import React from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import InteractionForm from './components/InteractionForm';
import ChatPanel from './components/ChatPanel';
import ToastContainer from './components/ToastContainer';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <div className="h-screen bg-[#f3f6f9] py-6 px-8 flex justify-center font-sans overflow-hidden">
        <div className="w-full max-w-7xl flex gap-6 items-stretch h-[calc(100vh-48px)]">
          {/* Left Column (65%) */}
          <div className="w-[65%] flex flex-col gap-4 h-full">
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight pl-1 flex-shrink-0">
              Log HCP Interaction
            </h1>
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-y-auto flex-1">
              <InteractionForm />
            </div>
          </div>

          {/* Right Column (35%) */}
          <div className="w-[35%] bg-white border border-slate-200 rounded-lg shadow-sm h-full overflow-hidden">
            <ChatPanel />
          </div>
        </div>
        
        {/* Global Toast Notifications */}
        <ToastContainer />
      </div>
    </Provider>
  );
};

export default App;
