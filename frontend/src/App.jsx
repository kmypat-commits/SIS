import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ProjectPage from './pages/ProjectPage';
import CDEPage from './pages/CDEPage';
import KnowledgePage from './pages/KnowledgePage';
import OptimizePage from './pages/OptimizePage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <main className="main-panel">
          <Routes>
            <Route path="/" element={<Navigate to="/project" replace />} />
            <Route path="/project"   element={<ProjectPage />} />
            <Route path="/cde"       element={<CDEPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/optimize"  element={<OptimizePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
