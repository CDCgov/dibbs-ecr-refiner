import { Routes, Route } from 'react-router';
import { Home } from './pages/Home';
import Demo from './pages/Demo';
import NotFound from './pages/NotFound';

function App() {
  return (
    <Routes>
      <Route index element={<Home />} />
      <Route path="demo" element={<Demo />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
