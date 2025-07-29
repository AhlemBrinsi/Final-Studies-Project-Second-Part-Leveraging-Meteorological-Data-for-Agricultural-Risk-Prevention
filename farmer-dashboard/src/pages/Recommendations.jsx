import { useState, useEffect } from "react";

export default function Recommendations() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/recommendations")
      .then(res => res.json())
      .then(setData);
  }, []);

  if (!data) return <div className="text-center mt-20">Loading...</div>;

  return (
    <div className="flex flex-col items-center justify-start min-h-screen px-4 pt-2">
      <h1 className="text-3xl font-bold text-green-800  mb-4 mt-0">Agricultural Recommendations</h1>

      <div className="flex flex-wrap gap-6 justify-center">
        {data.daily.map((day) => (
          <div
            key={day.date}
            className="w-80 p-6 rounded-2xl shadow-lg bg-white transform transition-transform duration-300 hover:scale-105 hover:shadow-2xl"
          >
            <h2 className="text-lg font-semibold text-green-700">
              {day.day_name} – {day.date}
            </h2>
            <p className="text-base mb-2">{day.weather}</p>

            <div className="mt-4 space-y-3 text-sm text-gray-700">
              <div>
                <strong>Irrigation:</strong><br />
                Priority: {day.irrigation.priority}<br />
                Frequency: {day.irrigation.frequency}<br />
                Amount: {day.irrigation.amount}<br />
                Best time: {day.irrigation.best_timing}<br />
                Notes: {day.irrigation.notes.join(", ")}
              </div>

              <div>
                <strong>Pest Control:</strong><br />
                Threat level: {day.pest.overall}<br />
                Threats: {day.pest.threats.join(", ")}<br />
                Prevention: {day.pest.prevention.join(", ")}
              </div>

              <div>
                <strong>Planting:</strong><br />
                Conditions: {day.planting.conditions}<br />
                Suggested Crops: {day.planting.crops.join(", ")}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
