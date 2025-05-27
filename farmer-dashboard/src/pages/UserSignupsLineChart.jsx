import { Bar } from 'react-chartjs-2';
import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const monthLabels = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export default function SignupsPerDayBarChart() {
  const [signupsPerDay, setSignupsPerDay] = useState({});
  const [selectedMonth, setSelectedMonth] = useState(1); // default January

  useEffect(() => {
    axios.get('/api/analytics/signups-per-day')
      .then(res => {
        setSignupsPerDay(res.data.signupsPerDay);
      })
      .catch(err => console.error('Failed to load signup data:', err));
  }, []);

  // Prepare labels for days in month
  const daysInMonth = signupsPerDay[selectedMonth]?.length || 30;
  const dayLabels = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  const data = {
    labels: dayLabels,
    datasets: [
      {
        label: `User Signups in ${monthLabels[selectedMonth - 1]}`,
        data: signupsPerDay[selectedMonth] || [],
        backgroundColor: '#10b981',
        borderRadius: 4,
      }
    ]
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-4">Daily User Signups per Month</h3>
      
      <select
        value={selectedMonth}
        onChange={e => setSelectedMonth(Number(e.target.value))}
        className="mb-4 p-2 border rounded"
      >
        {monthLabels.map((name, idx) => (
          <option key={idx} value={idx + 1}>{name}</option>
        ))}
      </select>

      <Bar data={data} />
    </div>
  );
}
