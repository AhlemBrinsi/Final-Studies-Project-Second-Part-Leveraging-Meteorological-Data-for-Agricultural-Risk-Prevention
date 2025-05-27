import { Bar } from 'react-chartjs-2';
import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function SupportTicketsByUserChart() {
  const [labels, setLabels] = useState([]);
  const [counts, setCounts] = useState([]);

  useEffect(() => {
    axios.get('/api/analytics/tickets-by-user')
      .then(res => {
        setLabels(res.data.map(u => u.username));
        setCounts(res.data.map(u => u.count));
      })
      .catch(console.error);
  }, []);

  const data = {
    labels,
    datasets: [{
      label: 'Tickets by User',
      data: counts,
      backgroundColor: '#6366f1',
    }],
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-2">Tickets by User</h3>
      <Bar data={data} />
    </div>
  );
}
