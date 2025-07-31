import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  FaTemperatureHigh,
  FaTint,
  FaWind,
  FaCloud,
} from "react-icons/fa";

const weatherCodeMap = {
  0: "Clear Sky ☀️",
  1: "Mainly Clear 🌤",
  2: "Partly Cloudy ⛅",
  3: "Cloudy ☁️",
  45: "Fog 🌫",
  48: "Fog 🌫",
  51: "Light Drizzle 🌦",
  53: "Moderate Drizzle 🌧",
  55: "Heavy Drizzle 🌧",
  61: "Light Rain 🌦",
  63: "Moderate Rain 🌧",
  65: "Heavy Rain 🌧",
  71: "Light Snow ❄️",
  73: "Moderate Snow ❄️",
  75: "Heavy Snow ❄️",
  95: "Thunderstorm ⛈",
};

function mapWeatherCodeToLabel(code) {
  return weatherCodeMap[code] || "Unknown";
}

const IconMap = {
  Temperature: <FaTemperatureHigh className="text-red-500 text-xl" />,
  Humidity: <FaTint className="text-blue-500 text-xl" />,
  "Wind Speed": <FaWind className="text-yellow-600 text-xl" />,
  "Cloud Cover": <FaCloud className="text-gray-600 text-xl" />,
};

const InfoCard = ({ title, minValue, maxValue, unit }) => (
  <div className="bg-white rounded-xl p-3 shadow-md flex items-center gap-3 min-w-[155px] transition-shadow duration-300 hover:shadow-xl">
    {React.cloneElement(IconMap[title], { className: IconMap[title].props.className.replace('text-2xl', 'text-xl') })}
    <div>
      <h4 className="font-semibold text-gray-700 text-sm">{title}</h4>
      <p className="text-xs text-gray-600">
        <strong>Max:</strong> {maxValue}{unit}
      </p>
      <p className="text-xs text-gray-600">
        <strong>Min:</strong> {minValue}{unit}
      </p>
    </div>
  </div>
);

const WeatherDashboard = () => {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);
  const [historicalData, setHistoricalData] = useState([]);
  const [showTodayDetails, setShowTodayDetails] = useState(false);
  const [showUpcomingDays, setShowUpcomingDays] = useState(false);
  // Changed from single index to array of expanded indexes
  const [expandedSmallCards, setExpandedSmallCards] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/api/weather")
      .then((res) => res.json())
      .then((data) => {
        setWeather(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching weather data:", err);
        setLoading(false);
      });

    fetch("http://localhost:5000/api/test-data-last-week?all=true")
      .then((res) => res.json())
      .then((data) => {
        const mapped = data
          .map((d) => ({
            date: d.date.replace(/"/g, ""),
            temp_max: d["temperature_2m_max (°C)"],
            temp_min: d["temperature_2m_min (°C)"],
            humidity_max: d["relative_humidity_2m_max (%)"],
            humidity_min: d["relative_humidity_2m_min (%)"],
            windspeed_max: d["wind_speed_10m_max (km/h)"],
            windspeed_min: d["wind_speed_10m_min (km/h)"],
            cloudcover_max: d["cloud_cover_max (%)"],
            cloudcover_min: d["cloud_cover_min (%)"],
            weather_condition: mapWeatherCodeToLabel(d.weather_code),
          }))
          .sort((a, b) => new Date(a.date) - new Date(b.date));
        setHistoricalData(mapped);
      })
      .catch((err) => console.error("Error fetching test data:", err));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!weather || !weather.predicted_dates) return <div>No weather data available.</div>;

  const latestRecord = historicalData.at(-1);

  const tempChartData = historicalData.map(({ date, temp_max, temp_min }) => ({
    date: date.slice(5),
    "Max Temp": temp_max,
    "Min Temp": temp_min,
  }));

  const humidityChartData = historicalData.map(({ date, humidity_max, humidity_min }) => ({
    date: date.slice(5),
    "Max Humidity": humidity_max,
    "Min Humidity": humidity_min,
  }));

  return (
    <div className="weather-page p-4 min-h-screen flex flex-col items-center space-y-8 max-w-6xl mx-auto">
      {/* Today's Weather Overview Card */}
      <div
        className="bg-white border shadow-md rounded-xl p-10 w-full cursor-pointer hover:shadow-xl transition-shadow duration-300"
        onClick={() => setShowTodayDetails((prev) => !prev)}
        aria-expanded={showTodayDetails}
        aria-controls="today-details"
      >
        <h2 className="text-2xl font-bold mb-4 text-center text-gray-700">
          Today's Weather Overview {latestRecord && `(${latestRecord.date})`}
        </h2>
        <p className="text-xl mb-4 text-center font-semibold">
          {latestRecord ? latestRecord.weather_condition : "No data"}
        </p>

        {showTodayDetails && latestRecord && (
          <>
            <div className="flex flex-wrap justify-center gap-6 mb-6">
              <InfoCard
                title="Temperature"
                maxValue={latestRecord.temp_max?.toFixed(1)}
                minValue={latestRecord.temp_min?.toFixed(1)}
                unit="°C"
              />
              <InfoCard
                title="Humidity"
                maxValue={latestRecord.humidity_max?.toFixed(1)}
                minValue={latestRecord.humidity_min?.toFixed(1)}
                unit="%"
              />
              <InfoCard
                title="Wind Speed"
                maxValue={latestRecord.windspeed_max?.toFixed(1)}
                minValue={latestRecord.windspeed_min?.toFixed(1)}
                unit=" km/h"
              />
              <InfoCard
                title="Cloud Cover"
                maxValue={latestRecord.cloudcover_max?.toFixed(1)}
                minValue={latestRecord.cloudcover_min?.toFixed(1)}
                unit="%"
              />
            </div>

            {/* Charts */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
              <div className="bg-white rounded-xl shadow-md p-4 transition-shadow hover:shadow-xl">
                <h3 className="text-xl font-semibold text-red-600 text-center mb-4">
                  Last Week Temperature
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={tempChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" angle={-30} textAnchor="end" height={60} interval={0} />
                    <YAxis />
                    <Tooltip />
                    <Legend
                      layout="vertical"
                      verticalAlign="top"
                      align="right"
                      wrapperStyle={{ padding: 10 }}
                    />
                    <Line type="monotone" dataKey="Max Temp" stroke="#F44336" />
                    <Line type="monotone" dataKey="Min Temp" stroke="#2196F3" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-xl shadow-md p-4 transition-shadow hover:shadow-xl">
                <h3 className="text-xl font-semibold text-blue-600 text-center mb-4">
                  Last Week Humidity
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={humidityChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" angle={-30} textAnchor="end" height={60} interval={0} />
                    <YAxis />
                    <Tooltip />
                    <Legend
                      layout="vertical"
                      verticalAlign="top"
                      align="right"
                      wrapperStyle={{ padding: 10 }}
                    />
                    <Line type="monotone" dataKey="Max Humidity" stroke="#3F51B5" />
                    <Line type="monotone" dataKey="Min Humidity" stroke="#00BCD4" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Upcoming Days Forecast */}
      <div
        className="bg-white border shadow-md rounded-xl p-6 w-full cursor-pointer hover:shadow-xl transition-shadow duration-300"
        onClick={() => {
          setShowUpcomingDays((prev) => {
            if (prev) setExpandedSmallCards([]); // reset expanded cards when closing
            return !prev;
          });
        }}
        aria-expanded={showUpcomingDays}
        aria-controls="upcoming-cards"
      >
        <h2 className="text-2xl font-bold mb-4 text-center text-gray-700 cursor-pointer">
          Upcoming Days Weather
        </h2>

        {/* Show small cards when expanded */}
        {showUpcomingDays && (
          <div className="grid md:grid-cols-3 gap-6" id="upcoming-cards">
            {weather.predicted_dates.slice(0, 3).map((date, index) => (
              <div
                key={index}
                className="bg-white rounded-xl shadow-md p-4 transition-shadow hover:shadow-xl cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation(); // Prevent toggling the parent on card click
                  setExpandedSmallCards((prev) => {
                    if (prev.includes(index)) {
                      // collapse if already expanded
                      return prev.filter((i) => i !== index);
                    } else {
                      // expand this card alongside others
                      return [...prev, index];
                    }
                  });
                }}
              >
                <h3 className="text-lg font-semibold mb-2">{date}</h3>
                <p className="text-xl mb-4">{weather.weather_condition[index]}</p>

                {/* Show detailed info if expanded */}
                {expandedSmallCards.includes(index) && (
                  <div className="flex gap-1">
                    <InfoCard
                      title="Temperature"
                      maxValue={weather.temp_max[index]?.toFixed(1)}
                      minValue={weather.temp_min[index]?.toFixed(1)}
                      unit="°C"
                    />
                    <InfoCard
                      title="Humidity"
                      maxValue={weather.humidity_max[index]?.toFixed(1)}
                      minValue={weather.humidity_min[index]?.toFixed(1)}
                      unit="%"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {!showUpcomingDays && (
          <p className="text-center text-gray-600 mt-4">Click Here</p>
        )}
      </div>
    </div>
  );
};

export default WeatherDashboard;
