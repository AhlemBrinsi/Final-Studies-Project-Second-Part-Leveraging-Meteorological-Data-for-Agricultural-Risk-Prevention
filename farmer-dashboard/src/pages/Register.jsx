// Register.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('client');
  const [ownerCode, setOwnerCode] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const response = await fetch('http://localhost:5000/api/users/register',  {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, role, ownerCode }),
      });

      const data = await response.json();

      if (response.ok) {
        alert('Registration successful. Please log in.');
        navigate('/login');
      } else {
        setError(data.message || 'Registration failed');
      }
    } catch (err) {
      setError('Error: ' + err.message);
    }
  };

  return (
  <div className="w-screen h-screen flex items-center justify-center bg-gray-100">
    <div className="w-full max-w-md p-6 bg-white rounded shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Register</h2>

      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <label className="block mb-2 font-semibold">Username</label>
        <input
          type="text"
          className="w-full border px-3 py-2 mb-4 rounded"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <label className="block mb-2 font-semibold">Email</label>
        <input
          type="email"
          className="w-full border px-3 py-2 mb-4 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label className="block mb-2 font-semibold">Password</label>
        <input
          type="password"
          className="w-full border px-3 py-2 mb-4 rounded"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <label className="block mb-2 font-semibold">Role</label>
        <select
          className="w-full border px-3 py-2 mb-4 rounded"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          <option value="client">Client</option>
          <option value="owner">Owner</option>
        </select>

        {role === 'owner' && (
          <>
            <label className="block mb-2 font-semibold">Owner Code</label>
            <input
              type="text"
              className="w-full border px-3 py-2 mb-4 rounded"
              value={ownerCode}
              onChange={(e) => setOwnerCode(e.target.value)}
              required
            />
          </>
        )}

        <button
          className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
          type="submit"
        >
          Register
        </button>
      </form>
    </div>
  </div>
);

}
