import { Layout } from './components/Layout';
import { Routes, Route } from 'react-router';
import { Home } from './pages/Home';
import UploadZip from './pages/UploadZip';
import NotFound from './pages/NotFound';

function App() {
  return (
    <Layout>
      <Routes>
        <Route index element={<Home />} />
        <Route path="zip" element={<UploadZip />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
