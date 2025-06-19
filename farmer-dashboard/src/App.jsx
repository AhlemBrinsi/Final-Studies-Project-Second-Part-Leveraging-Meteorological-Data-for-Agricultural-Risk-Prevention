import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Login from './pages/Login.jsx';
import ClientDashboard from './pages/ClientDashboard.jsx';
import OwnerDashboard from './pages/OwnerDashboard.jsx';
import PrivateRoute from "./pages/PrivateRoute.jsx";
import Register from './pages/Register.jsx';
import ResetPassword from './pages/ResetPassword.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import OwnerProfile from './pages/OwnerProfile.jsx';
import ClientProfile from './pages/ClientProfile.jsx';
import UserManagement from './pages/UserManagement.jsx'; 
import ArticlesDashboard from './pages/ArticlesDashboard.jsx';
import ViewArticles from './pages/ViewArticles.jsx';
import AdminSupport from './pages/AdminSupport.jsx';
import ClientSupport from './pages/ClientSupport.jsx';
import Logs from './pages/Logs.jsx';
import Analytics from './pages/Analytics.jsx';
import WeatherDashboard from './pages/WeatherDashboard.jsx';
export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/weather" element={<WeatherDashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/client-support" element={<ClientSupport />} />
        <Route path="/admin-support" element={<AdminSupport />} />
        <Route path="/view-articles" element={<ViewArticles />} />
        <Route path="/articles" element={<ArticlesDashboard />} />
        <Route path="/user_management" element={<UserManagement />} />
        <Route path="/client-profile" element={<ClientProfile />} />
        <Route path="/owner-profile" element={<OwnerProfile />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/client-dashboard"
          element={
            <PrivateRoute role="client">
              <ClientDashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/owner-dashboard"
          element={
            <PrivateRoute role="owner">
              <OwnerDashboard />
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Login />} />
      </Routes>
    </Router>
  );
}
