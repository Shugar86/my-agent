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
import ShowcasePage from './pages/ShowcasePage';
import DemoPage from './pages/DemoPage';

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
          <Route path="demo" element={<DemoPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="builder" element={<Navigate to="/settings?tab=agents" replace />} />
          <Route path="agents" element={<Navigate to="/settings?tab=agents" replace />} />
          <Route path="knowledge" element={<Navigate to="/settings?tab=knowledge" replace />} />
          <Route path="mcp" element={<Navigate to="/settings?tab=mcp" replace />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
        <Route path="onboarding" element={<OnboardingPage />} />
        <Route path="share/templates/:templateId" element={<PublicTemplatePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
