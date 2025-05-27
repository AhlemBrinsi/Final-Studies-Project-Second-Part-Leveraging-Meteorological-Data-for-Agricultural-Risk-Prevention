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
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

export default function ArticlesPerDayChart() {
  const [articlesPerDay, setArticlesPerDay] = useState({});
  const [selectedMonth, setSelectedMonth] = useState(1);

  useEffect(() => {
    axios.get('/api/analytics/articles-per-day')
      .then(res => {
        setArticlesPerDay(res.data.articlesPerDay || {});
      })
      .catch(err => console.error(err));
  }, []);

  // Prepare data for the chart based on selected month
  const daysData = articlesPerDay[selectedMonth] || [];

  // Generate day labels for the selected month
  const dayLabels = daysData.map((_, i) => (i + 1).toString());

  const data = {
    labels: dayLabels,
    datasets: [
      {
        label: `Articles Published in ${monthLabels[selectedMonth - 1]}`,
        data: daysData,
        backgroundColor: '#3b82f6',
        borderRadius: 6,
      }
    ],
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-4">Articles Published Per Day</h3>

      <label htmlFor="month-select" className="block mb-2 font-medium">
        Select Month:
      </label>
      <select
        id="month-select"
        value={selectedMonth}
        onChange={(e) => setSelectedMonth(Number(e.target.value))}
        className="mb-6 p-2 border rounded"
      >
        {monthLabels.map((label, idx) => (
          <option key={idx} value={idx + 1}>{label}</option>
        ))}
      </select>

      <Bar data={data} />
    </div>
  );
}
