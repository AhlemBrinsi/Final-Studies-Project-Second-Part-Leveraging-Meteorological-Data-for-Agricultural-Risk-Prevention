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

export default function ArticlesPerUserChart() {
  const [userData, setUserData] = useState([]);

  useEffect(() => {
    axios.get('/api/analytics/articles-per-user')
      .then(res => {
        setUserData(res.data.articlesPerUser);
      })
      .catch(err => console.error(err));
  }, []);

  // Extract usernames and counts
  const labels = userData.map(u => u.username || u.userId);
  const counts = userData.map(u => u.count);

  const data = {
    labels,
    datasets: [
      {
        label: 'Articles Published',
        data: counts,
        backgroundColor: '#10b981', // teal-ish color
        borderRadius: 6,
      }
    ]
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-2">Articles Published by User</h3>
      <Bar data={data} />
    </div>
  );
}
