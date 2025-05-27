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

export default function SupportStatusBarChart() {
  const [labels, setLabels] = useState(['Open', 'Closed']);
  const [counts, setCounts] = useState([0, 0]);

  useEffect(() => {
    axios.get('/api/analytics/status-counts')
      .then(res => {
        // Assuming res.data has shape: { open: Number, closed: Number }
        setCounts([res.data.open, res.data.closed]);
      })
      .catch(err => console.error('Error fetching support status counts:', err));
  }, []);

  const data = {
    labels,
    datasets: [
      {
        label: 'Support Ticket Status',
        data: counts,
        backgroundColor: ['#facc15', '#10b981'], // yellow and green
        borderRadius: 5,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => ` ${context.parsed.y} tickets`
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-4">Ticket Status</h3>
      <Bar data={data} options={options} />
    </div>
  );
}
