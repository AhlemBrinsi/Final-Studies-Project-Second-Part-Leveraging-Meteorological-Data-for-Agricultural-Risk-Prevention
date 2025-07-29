import React, { useEffect, useState } from 'react';

const WeatherDashboard = () => {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:5000/api/weather')
      .then(res => res.json())
      .then(data => {
        setWeather(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching weather data:', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!weather || !weather.predicted_dates) return <div>No weather data available.</div>;

  return (
    <div className="weather-page p-4 min-h-screen items-center justify-start">
      <h2 className="text-3xl font-bold text-green-800  mb-4 mt-0 text-center">3-Day Weather Forecast</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl">
        {weather.predicted_dates.map((date, index) => (
          <div
            key={index}
            className="bg-white border shadow-md rounded-xl p-6 transform transition-transform duration-300 hover:scale-105 hover:shadow-2xl"
          >
            <h3 className="text-lg font-semibold mb-2">{date}</h3>
            <p className="text-xl mb-4">{weather.weather_condition[index]}</p>
            <div className="space-y-1 text-base">
              <p><strong>Max Temp:</strong> {weather.temp_max[index].toFixed(1)}°C</p>
              <p><strong>Min Temp:</strong> {weather.temp_min[index].toFixed(1)}°C</p>
              <p><strong>Max Humidity:</strong> {weather.humidity_max[index].toFixed(1)}%</p>
              <p><strong>Min Humidity:</strong> {weather.humidity_min[index].toFixed(1)}%</p>
            </div>
          </div>
        ))}

      </div>
    </div>
  );
};

export default WeatherDashboard;
