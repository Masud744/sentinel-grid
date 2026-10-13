import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import DashboardPage from './pages/DashboardPage';
import IncidentTimelinePage from './pages/IncidentTimelinePage';
import AdminPage from './pages/AdminPage';
import LoginPage from './pages/LoginPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <WebSocketProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/incidents" element={<IncidentTimelinePage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/login" element={<LoginPage />} />
          </Routes>
        </BrowserRouter>
      </WebSocketProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
