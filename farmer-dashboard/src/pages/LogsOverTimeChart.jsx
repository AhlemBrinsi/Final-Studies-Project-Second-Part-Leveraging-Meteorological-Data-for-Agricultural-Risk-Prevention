import { Line } from 'react-chartjs-2';
import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend,Filler );

export default function LogsOverTimeChart() {
  const [labels, setLabels] = useState([]);
  const [counts, setCounts] = useState([]);

  useEffect(() => {
    axios.get('/api/analytics/logs-over-time')
      .then(res => {
        setLabels(res.data.labels);
        setCounts(res.data.counts);
      })
      .catch(err => console.error('Failed to load logs over time:', err));
  }, []);

  const data = {
    labels,
    datasets: [{
      label: 'Logs per Day',
      data: counts,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.3)',
      fill: true,
      tension: 0.4,
    }],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
    },
  };

  return (
    <div className="bg-white p-4 rounded-2xl shadow-md mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-2">Logs Over Time</h3>
      <Line data={data} options={options} />
    </div>
  );
}
