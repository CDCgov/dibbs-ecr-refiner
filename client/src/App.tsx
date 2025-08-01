import { Routes, Route } from 'react-router';
import { Configurations } from './pages/Configurations';
import Testing from './pages/Testing';
import NotFound from './pages/NotFound';
import { Layout } from './components/Layout';
import { useLogin } from './hooks/Login';
import { Home } from './pages/Home';
import { ToastContainer } from 'react-toastify';

function App() {
  const [user, isLoading] = useLogin();
  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (!user)
    return (
      <Routes>
        <Route index element={<Home />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    );
  return (
    <Layout>
      <ToastContainer />
      <Routes>
        <Route index element={<Configurations />} />
        <Route path="testing" element={<Testing />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
