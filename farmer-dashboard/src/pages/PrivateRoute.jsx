import React from 'react';
import { Navigate } from 'react-router-dom';

export default function PrivateRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user'));
  if (!user) {
    // Not logged in, redirect to login page
    return <Navigate to="/" />;
  }
  // Logged in, render the child components
  return children;
}
