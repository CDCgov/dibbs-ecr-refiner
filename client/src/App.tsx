import { Routes, Route, Navigate } from 'react-router';
import { Configurations } from './pages/Configurations';
import Testing from './pages/Testing';
import NotFound from './pages/NotFound';
import { Layout } from './components/Layout';
import { useLogin } from './hooks/Login';
import { Home } from './pages/Home';
import ConfigurationDetail from './pages/ConfigurationDetail';

function App() {
  const [user, isLoading] = useLogin();
  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (!user)
    return (
      <Routes>
        <Route path="/" index element={<Home />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    );
  return (
    <Layout>
      <Routes>
        {/* this is the home page for authenticated users */}
        <Route path="/" element={<Navigate to="/configurations" replace />} />

        <Route path="/configurations" element={<Configurations />} />
        <Route path="/configurations/:id" element={<ConfigurationDetail />} />
        <Route path="/testing" element={<Testing />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
