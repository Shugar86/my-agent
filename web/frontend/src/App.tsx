import { lazy, Suspense } from 'react';
import './layout/theme.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './layout/AppShell';
import Dashboard from './pages/Dashboard';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import WorkflowList from './pages/WorkflowList';
import AnalyticsPage from './pages/AnalyticsPage';
import AdminPage from './pages/AdminPage';
import OnboardingPage from './pages/OnboardingPage';
import PublicTemplatePage from './pages/PublicTemplatePage';
import AgentsPage from './pages/AgentsPage';
import KnowledgePage from './pages/KnowledgePage';
import McpPage from './pages/McpPage';
import ShowcasePage from './pages/ShowcasePage';

const WorkflowBuilder = lazy(() => import('./pages/WorkflowBuilder'));
const MarketplacePage = lazy(() => import('./pages/MarketplacePage'));

function PageFallback() {
  return (
    <div style={{ padding: 30 }}>
      <div className="skeleton" style={{ height: 48, width: 240, marginBottom: 16 }} />
      <div className="skeleton" style={{ height: 200 }} />
    </div>
  );
}

function LazyPage({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageFallback />}>{children}</Suspense>;
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="workflows" element={<WorkflowList />} />
          <Route path="workflows/:workflowId" element={<LazyPage><WorkflowBuilder /></LazyPage>} />
          <Route path="marketplace" element={<LazyPage><MarketplacePage /></LazyPage>} />
          <Route path="showcase" element={<ShowcasePage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="builder" element={<Navigate to="/agents" replace />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="mcp" element={<McpPage />} />
        </Route>
        <Route path="onboarding" element={<OnboardingPage />} />
        <Route path="share/templates/:templateId" element={<PublicTemplatePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
