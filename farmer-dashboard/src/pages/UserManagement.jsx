import { useEffect, useState } from 'react';
import axios from 'axios';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');


  useEffect(() => {
    axios.get('/api/users', {
      headers: {
        Authorization: `Bearer ${'token'}`
      }
    }).then(res => {
      // Make sure res.data is an array
      if (Array.isArray(res.data)) {
        setUsers(res.data);
      } else {
        console.error('Expected users array but got:', res.data);
      }
    }).catch(err => {
      console.error('Failed to fetch users:', err);
    });
  }, []);

  const toggleVerification = async (id, currentStatus) => {
    try {
      const res = await axios.patch(`/api/users/${id}/verify`, {
        verified: !currentStatus
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      setUsers(users.map(u => u._id === id ? res.data : u));
    } catch (err) {
      console.error('Failed to toggle verification:', err);
    }
  };

  const deleteUser = async (id) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    try {
      await axios.delete(`/api/users/${id}`, {
        headers: {
          Authorization: `Bearer ${'token'}`
        }
      });
      setUsers(users.filter(u => u._id !== id));
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  const viewUser = (user) => {
    alert(`
Username: ${user.username}
Email: ${user.email}
Role: ${user.role}
Job: ${user.job}
Age: ${user.age}
Bio: ${user.bio}
Verified: ${user.verified ? 'Yes' : 'No'}
    `);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Users Management</h2>
      <div className="overflow-auto rounded-lg shadow">
        <table className="w-full table-auto text-sm text-left">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-3">Username</th>
              <th className="p-3">Email</th>
              <th className="p-3">Role</th>
              <th className="p-3">Verified</th>
              <th className="p-3">Job</th>
              <th className="p-3">Age</th>
              <th className="p-3">Bio</th>
              <th className="p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user._id} className="border-t">
                <td className="p-3 flex items-center gap-3">
                  <img
                    src={
                      user.profilePicture
                        ? user.profilePicture.startsWith("/uploads")
                          ? `http://localhost:5000${user.profilePicture}`
                          : user.profilePicture
                        : "/ava.jpg"
                    }
                    alt={user.username}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                  <span>{user.username}</span>
                </td>
                <td className="p-3">{user.email}</td>
                <td className="p-3 capitalize">{user.role}</td>
                <td className="p-3">{user.verified ? 'Yes' : 'No'}</td>
                <td className="p-3">{user.job}</td>
                <td className="p-3">{user.age}</td>
                <td className="p-3">{user.bio}</td>
                <td className="p-3 flex gap-2 flex-wrap">
                  <button
                    className="px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs"
                    onClick={() => viewUser(user)}
                  >
                    View
                  </button>
                  <button
                    className={`px-2 py-1 ${
                      user.verified ? 'bg-yellow-500' : 'bg-green-500'
                    } text-white rounded hover:opacity-80 text-xs`}
                    onClick={() => toggleVerification(user._id, user.verified)}
                  >
                    {user.verified ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs"
                    onClick={() => deleteUser(user._id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan="8" className="p-3 text-center text-gray-500">
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
