import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({
    user: '',
    eventType: '',
    severity: '',
    startDate: '',
    endDate: '',
    page: 1,
  });
  const [totalPages, setTotalPages] = useState(1);

  const fetchLogs = async () => {
    const params = { ...filters };
    try {
      const res = await axios.get('/api/logs', { params });
      setLogs(res.data.logs);
      setTotalPages(res.data.pages);
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value, page: 1 });
  };

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage });
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Admin Logs</h1>

      {/* Filters */}
      <div className="flex gap-4 mb-6 flex-wrap">
        <input
          name="user"
          value={filters.user}
          onChange={handleFilterChange}
          placeholder="User"
          className="border p-2 rounded"
        />
        <select name="eventType" value={filters.eventType} onChange={handleFilterChange} className="border p-2 rounded">
          <option value="">All Event Types</option>
          <option value="LOGIN">LOGIN</option>
          <option value="FAILED_LOGIN">FAILED_LOGIN</option>
          <option value="EMAIL_VERIFICATION_FAILED">EMAIL_VERIFICATION_FAILED</option>
          <option value="USER_DELETE">USER_DELETE</option>
          <option value="PROFILE_EDIT">PROFILE_EDIT</option>
          <option value="REGISTER">REGISTER</option>
          <option value="EMAIL_VERIFICATION">EMAIL_VERIFICATION</option>
          <option value="PASSWORD_RESET_REQUEST">PASSWORD_RESET_REQUEST</option>
          <option value="PASSWORD_RESET">PASSWORD_RESET</option>
          <option value="MANUAL_VERIFICATION">MANUAL_VERIFICATION</option>
          <option value="ARTICLE_CREATE">ARTICLE_CREATE</option>
          <option value="ARTICLE_EDIT">ARTICLE_EDIT</option>
          <option value="ARTICLE_DELETE">ARTICLE_DELETE</option>
          <option value="FEEDBACK_CREATE">FEEDBACK_CREATE</option>
          <option value="FEEDBACK_EDIT">FEEDBACK_EDIT</option>
          <option value="FEEDBACK_DELETE">FEEDBACK_DELETE</option>
          <option value="SUPPORT_CREATE">SUPPORT_CREATE</option>
          <option value="SUPPORT_RESPONSE">SUPPORT_RESPONSE</option>
          {/* Add more options */}
        </select>
        <select name="severity" value={filters.severity} onChange={handleFilterChange} className="border p-2 rounded">
          <option value="">All Severities</option>
          <option value="INFO">INFO</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
        </select>
        <input type="date" name="startDate" value={filters.startDate} onChange={handleFilterChange} className="border p-2 rounded" />
        <input type="date" name="endDate" value={filters.endDate} onChange={handleFilterChange} className="border p-2 rounded" />
      </div>

      {/* Logs Table */}
      <table className="min-w-full border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2 border">Timestamp</th>
            <th className="p-2 border">User</th>
            <th className="p-2 border">Event Type</th>
            <th className="p-2 border">Severity</th>
            <th className="p-2 border">Description</th>
            <th className="p-2 border">IP Address</th>
          </tr>
        </thead>
        <tbody>
          {logs.length === 0 ? (
            <tr>
              <td colSpan="6" className="text-center p-4">No logs found</td>
            </tr>
          ) : (
            logs.map((log) => (
              <tr key={log._id} className="hover:bg-gray-50">
                <td className="p-2 border">{new Date(log.timestamp).toLocaleString()}</td>
                <td className="p-2 border">{log.username || '-'}</td>
                <td className="p-2 border">{log.eventType}</td>
                <td className={`p-2 border font-semibold
                  ${log.severity === 'ERROR' ? 'text-red-600' : log.severity === 'WARN' ? 'text-yellow-600' : 'text-green-600'}`}>
                  {log.severity}
                </td>
                <td className="p-2 border truncate max-w-xs" title={log.description}>{log.description}</td>
                <td className="p-2 border">{log.ipAddress || '-'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="mt-4 flex justify-center gap-2">
        {[...Array(totalPages)].map((_, i) => (
          <button
            key={i}
            onClick={() => handlePageChange(i + 1)}
            className={`px-3 py-1 rounded border ${filters.page === i + 1 ? 'bg-blue-500 text-white' : 'bg-white'}`}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  );
}
