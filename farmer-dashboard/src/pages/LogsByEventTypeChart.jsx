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

export default function LogsByEventTypeChart() {
  const [labels, setLabels] = useState([]);
  const [counts, setCounts] = useState([]);

  useEffect(() => {
    axios.get('/api/analytics/logs-by-event-type')
      .then(res => {
        setLabels(res.data.labels);
        setCounts(res.data.counts);
      })
      .catch(err => console.error('Error fetching logs by event type:', err));
  }, []);

  const data = {
    labels,
    datasets: [
      {
        label: 'Number of Events',
        data: counts,
        backgroundColor: '#3b82f6', // Tailwind blue-500
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
          label: (context) => ` ${context.parsed.y} logs`
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
      <h3 className="text-lg font-semibold text-gray-700 mb-4">Logs by Event Type</h3>
      <Bar data={data} options={options} />
    </div>
  );
}
