import { Routes, Route, Navigate } from 'react-router';
import { Configurations } from './pages/Configurations';
import { Simulator } from './pages/Simulator';
import { NotFound } from './pages/NotFound';
import { Layout } from '@components/Layout';
import { useLogin } from './hooks/useLogin';
import { Home } from './pages/Home';
import { ToastContainer } from 'react-toastify';
import { ConfigBuild } from './pages/Configurations/ConfigBuild';
import { ConfigTest } from './pages/Configurations/ConfigTest';
import { ConfigActivate } from './pages/Configurations/ConfigActivate';
import 'react-toastify/dist/ReactToastify.css';
import { Spinner } from '@components/Spinner';
import { SessionRedirect } from './pages/SessionRedirect';
import { ActivityLog } from './pages/ActivityLog';
import { AppUpdates } from './pages/AppUpdates';
import { ConfigSerialized } from './pages/Configurations/ConfigSerialized';

export function App() {
  const { user, refreshUser, isLoading } = useLogin();

  if (isLoading) {
    return <Spinner variant="centered" />;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/" index element={<Home />} />
        <Route path="/expired" element={<SessionRedirect />} />
        <Route path="*" element={<SessionRedirect />} />
      </Routes>
    );
  }

  return (
    <Layout displayName={`${user.username} (${user.jurisdiction_id})`}>
      <ToastContainer className="bottom-5!" position="bottom-left" stacked />
      <Routes>
        {/* this is the home page for authenticated users */}
        <Route path="/" element={<Navigate to="/configurations" replace />} />
        <Route path="/activity" element={<ActivityLog />} />
        <Route
          path="/configurations"
          element={<Configurations user={user} refreshUser={refreshUser} />}
        />
        <Route path="/configurations/:id/build" element={<ConfigBuild />} />
        <Route path="/configurations/:id/test" element={<ConfigTest />} />
        <Route
          path="/configurations/:id/activate"
          element={<ConfigActivate />}
        />
        <Route
          path="/configurations/:id/serialized"
          element={<ConfigSerialized />}
        />
        <Route path="/app-updates" element={<AppUpdates />} />
        <Route path="/simulator" element={<Simulator />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}
