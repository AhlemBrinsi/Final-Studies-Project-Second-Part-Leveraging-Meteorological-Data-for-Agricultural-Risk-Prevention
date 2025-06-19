import { useState, useEffect } from 'react';

function ClientWeatherDashboard() {
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    const mockWeather = {
      today: {
        wind: '15 km/h',
        uv: '5',
        humidity: '70%',
        visibility: '10 km',
        temp: '30°C',
        icon: 'sunny',
      },
      forecast: [
        { date: '2025-06-20', icon: 'sunny', temp: '30°C' },
        { date: '2025-06-21', icon: 'cloudy', temp: '28°C' },
        { date: '2025-06-22', icon: 'rain', temp: '25°C' },
        { date: '2025-06-23', icon: 'storm', temp: '22°C' },
      ],
    };

    const timer = setTimeout(() => {
      setWeather(mockWeather);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  if (!weather) return <div className="text-gray-700 p-4">Loading...</div>;

  const { today, forecast } = weather;

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: '#ffffff' }}>
      <div className="max-w-6xl mx-auto space-y-10 text-gray-800">

        {/* Next 4 Days + Today */}
        <section>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-start">

            {/* TODAY CARD */}
            <div
              className="col-span-1 md:col-span-2 p-10 rounded-xl transition-all duration-300 transform hover:scale-105 hover:shadow-xl"
              style={{
                backgroundColor: '#f0f4f1',
                boxShadow: '0 0 12px #a7c95788',
                minHeight: '320px',
              }}
            >
              <div className="flex flex-col h-full justify-between">
                <div className="flex items-center space-x-6">
                  <div className="text-8xl">
                    {today.icon === 'sunny' && '☀️'}
                    {today.icon === 'cloudy' && '☁️'}
                    {today.icon === 'rain' && '🌧️'}
                    {today.icon === 'storm' && '⛈️'}
                  </div>
                  <div className="text-gray-800 space-y-2">
                    <p className="font-bold text-3xl" style={{ color: '#3a7d44' }}>Today</p>
                    <p className="text-lg">Wind: {today.wind}</p>
                    <p className="text-lg">Temp: {today.temp}</p>
                    <p className="text-lg">UV: {today.uv}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* FORECAST CARDS */}
            <div className="col-span-1 md:col-span-3 space-y-4">
              <h2 className="text-3xl font-semibold" style={{ color: '#3a7d44' }}>
                Next 4 Days
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {forecast.map((day, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-xl text-center transition-all duration-300 transform hover:scale-105 hover:shadow-xl"
                    style={{
                      backgroundColor: '#f0f4f1',
                      boxShadow: '0 0 10px #a7c95788',
                      minHeight: '160px',
                    }}
                  >
                    <p className="text-base font-medium mb-1" style={{ color: '#6b7280' }}>
                      {day.date.slice(5)}
                    </p>
                    <div className="text-4xl mb-2">
                      {day.icon === 'sunny' && '☀️'}
                      {day.icon === 'cloudy' && '☁️'}
                      {day.icon === 'rain' && '🌧️'}
                      {day.icon === 'storm' && '⛈️'}
                    </div>
                    <p className="text-xl font-semibold" style={{ color: '#3a7d44' }}>
                      {day.temp}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Today's Overview */}
        <section>
          <h2 className="text-3xl font-semibold mb-6" style={{ color: '#3a7d44' }}>
            Today's Overview
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {['Wind', 'UV Index', 'Humidity', 'Visibility'].map((label) => (
              <div
                key={label}
                className="p-6 rounded-xl text-center transition-all duration-300 transform hover:scale-105 hover:shadow-xl"
                style={{ backgroundColor: '#f0f4f1', boxShadow: '0 0 10px #a7c95788' }}
              >
                <h3 className="mb-2" style={{ color: '#6b7280' }}>{label}</h3>
                <p className="text-2xl font-bold" style={{ color: '#3a7d44' }}>
                  {today[label.toLowerCase().replace(' ', '')]}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default ClientWeatherDashboard;
