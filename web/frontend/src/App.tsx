import './layout/theme.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './layout/AppShell';
import Dashboard from './pages/Dashboard';
import MarketplacePage from './pages/MarketplacePage';
import ChatPage from './pages/ChatPage';
import AgentBuilderPage from './pages/AgentBuilderPage';
import SettingsPage from './pages/SettingsPage';
import WorkflowList from './pages/WorkflowList';
import WorkflowBuilder from './pages/WorkflowBuilder';

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="workflows" element={<WorkflowList />} />
          <Route path="workflows/:workflowId" element={<WorkflowBuilder />} />
          <Route path="marketplace" element={<MarketplacePage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="builder" element={<AgentBuilderPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
