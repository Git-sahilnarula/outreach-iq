import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import JobInput from './pages/JobInput';
import JobDetail from './pages/JobDetail';
import GmailSettings from './pages/GmailSettings';
import Automations from './pages/Automations';
import Layout from './components/Layout';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
        <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
        <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />
          <Route path="jobs/new" element={<JobInput />} />
          <Route path="jobs/:id" element={<JobDetail />} />
          {/* Phase 2: Gmail — also handles /gmail?connected=true and /gmail?error=... */}
          <Route path="gmail" element={<GmailSettings />} />
          {/* Phase 7: Automations & Webhooks */}
          <Route path="automations" element={<Automations />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
