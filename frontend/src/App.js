import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SignUp from './pages/SignUp';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ClassificationResults from './pages/ClassificationResults';
import QueryProcessing from './pages/QueryProcessing';
import ProfessionalsResults from './pages/ProfessionalsResults';
import Location from './pages/Location';
import './styles/App.css';

// Simple authentication check
const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

// Protected route component
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/signup" element={<SignUp />} />
          <Route path="/login" element={<Login />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/classification" 
            element={
              <ProtectedRoute>
                <ClassificationResults />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/processing" 
            element={
              <ProtectedRoute>
                <QueryProcessing />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/results" 
            element={
              <ProtectedRoute>
                <ProfessionalsResults />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/location" 
            element={
              <ProtectedRoute>
                <Location />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;