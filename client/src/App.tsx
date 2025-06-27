import { Routes, Route } from 'react-router';
import { Configurations } from './pages/Configurations';
import Testing from './pages/Testing';
import NotFound from './pages/NotFound';
import { Layout } from './components/Layout';

function App() {
  return (
    <Layout>
      <Routes>
        <Route index element={<Configurations />} />
        <Route path="testing" element={<Testing />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
