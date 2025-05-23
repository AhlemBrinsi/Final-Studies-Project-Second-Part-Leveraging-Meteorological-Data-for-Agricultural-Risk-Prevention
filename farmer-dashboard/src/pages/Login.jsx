import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();

  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/users/login',  {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emailOrUsername, password }),  // changed here
      });

      const data = await response.json();
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('userId', data.user.id); // Now correctly set
      //localStorage.setItem('userEmail', data.user.email); // or username

      if (response.ok) {

        if (data.user.role === 'client') {
          navigate('/client-dashboard');
        } else {
          navigate('/owner-dashboard');
        }
      } else {
        setError(data.message || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (

    <div className="w-screen h-screen flex items-center justify-center bg-gray-100">
        <div className="w-full max-w-md p-6 bg-white rounded shadow-md">
          <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>

          {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>
          )}

          <form onSubmit={handleSubmit}>
            <label className="block mb-2 font-semibold" htmlFor="emailOrUsername">
              Email or Username
            </label>
            <input
              id="emailOrUsername"
              type="text"
              className="w-full border px-3 py-2 mb-4 rounded"
              value={emailOrUsername}
              onChange={(e) => setEmailOrUsername(e.target.value)}
              required
            />

            <label className="block mb-2 font-semibold" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="w-full border px-3 py-2 mb-6 rounded"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
          <p className="mt-2 text-center">
          <Link to="/forgot-password" className="text-blue-600 hover:underline">Forgot Password?</Link>
          </p>
          <p className="mt-4 text-center">
            Don't have an account?{' '}
            <Link to="/register" className="text-blue-600 hover:underline">Register here</Link>
          </p>
        </div>
        </div>
  );
}
