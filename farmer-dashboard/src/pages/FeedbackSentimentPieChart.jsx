import { Pie } from 'react-chartjs-2';
import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function FeedbackSentimentPieChart() {
  const [data, setData] = useState({
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        label: 'Feedback Sentiment',
        data: [0, 0, 0],
        backgroundColor: ['#10b981', '#fbbf24', '#ef4444'],
        borderWidth: 1,
      },
    ],
  });

  useEffect(() => {
    axios.get('/api/analytics/feedback-sentiment')
      .then(res => {
        const counts = {
          positive: 0,
          neutral: 0,
          negative: 0,
          ...res.data, // assuming response is like { positive: x, neutral: y, negative: z }
        };

        setData({
          labels: ['Positive', 'Neutral', 'Negative'],
          datasets: [
            {
              label: 'Feedback Sentiment',
              data: [counts.positive, counts.neutral, counts.negative],
              backgroundColor: ['#10b981', '#fbbf24', '#ef4444'],
              borderWidth: 1,
            },
          ],
        });
      })
      .catch(err => console.error('Error loading sentiment data:', err));
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-md p-4 mt-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-2">Feedback Sentiment</h3>
      <Pie data={data} />
    </div>
  );
}
