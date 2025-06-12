import { Routes, Route } from 'react-router';
import { Home } from './pages/Home';
import Demo from './pages/Demo';
import NotFound from './pages/NotFound';
import { Layout } from './components/Layout';

function App() {
  return (
    <Layout>
      <Routes>
        <Route index element={<Home />} />
        <Route path="demo" element={<Demo />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
