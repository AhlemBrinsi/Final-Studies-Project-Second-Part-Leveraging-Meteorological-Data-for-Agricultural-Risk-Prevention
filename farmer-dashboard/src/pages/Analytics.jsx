import { useEffect, useState } from 'react';
import axios from 'axios';

import ArticlesPerDayChart from './ArticlesPerDayChart';
import ArticlesPerUserChart from './ArticlesPerUserChart';
import FeedbackSentimentPieChart from './FeedbackSentimentPieChart';
import LogsOverTimeChart from './LogsOverTimeChart';
import LogsByEventTypeChart from './LogsByEventTypeChart';
import SupportStatusBarChart from './SupportStatusChart';
import SupportTicketsByUserChart from './SupportTicketsByUserChart';
import UserSignupsLineChart from './UserSignupsLineChart';

export default function Analytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    axios.get('/api/analytics/summary')
      .then((res) => setData(res.data))
      .catch((err) => console.error('Failed to fetch analytics:', err));
  }, []);

  if (!data) return <p className="text-center mt-10">Loading...</p>;

  return (
    <>
      {/* Two columns: summary cards on left, user signups chart on right */}
      <div className="flex gap-6 p-6 items-start">
        {/* Left: Summary Cards in a vertical stack */}
        <div className="flex flex-col gap-3 w-1/2">
          <SummaryCard title="Users" count={data.users} />
          <SummaryCard title="Articles" count={data.articles} />
          <SummaryCard title="Feedbacks" count={data.feedbacks} />
          <SummaryCard title="Support Tickets" count={data.supportTickets} />
          <SummaryCard title="Logs" count={data.logs} />
        </div>

        {/* Right: User Signups chart */}
        <div className="w-1/2 bg-white shadow-lg rounded-2xl p-4">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">User Signups</h2>
          <UserSignupsLineChart />
        </div>
      </div>

      {/* Other charts section (unchanged) */}
      <div className="p-6 space-y-8">
        <div className="flex space-x-4">
          <div className="flex-1 border p-4 rounded shadow">
            <ArticlesPerDayChart />
          </div>
          <div className="flex-1 border p-4 rounded shadow">
            <ArticlesPerUserChart />
          </div>
          <div className="flex-1 border p-4 rounded shadow">
            <FeedbackSentimentPieChart />
          </div>
        </div>

        <div className="flex space-x-4">
          <div className="flex-1 border p-4 rounded shadow">
            <LogsOverTimeChart />
          </div>
          <div className="flex-1 border p-4 rounded shadow">
            <LogsByEventTypeChart />
          </div>
        </div>

        <div className="flex space-x-4">
          <div className="flex-1 border p-4 rounded shadow">
            <SupportStatusBarChart />
          </div>
          <div className="flex-1 border p-4 rounded shadow">
            <SupportTicketsByUserChart />
          </div>
        </div>
      </div>
    </>
  );
}


function SummaryCard({ title, count }) {
  return (
    <div className="bg-white shadow-lg rounded-2xl p-3 text-center">
      <h2 className="text-lg font-semibold text-gray-700">{title}</h2>
      <p className="text-2xl font-bold text-blue-600 mt-1">{count}</p>
    </div>
  );
}
