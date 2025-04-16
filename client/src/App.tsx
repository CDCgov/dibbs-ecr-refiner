import './App.css';
import { Layout } from './components/Layout';
import { Routes, Route } from 'react-router';
import { Home } from './pages/Home';
import About from './pages/About';

function App() {
  return (
    <Layout>
      <Routes>
        <Route index element={<Home />} />
        <Route path="about" element={<About />} />
      </Routes>
    </Layout>
  );
}

export default App;
