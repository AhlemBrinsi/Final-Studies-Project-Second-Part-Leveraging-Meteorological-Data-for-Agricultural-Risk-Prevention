import express from "express";
import { spawn } from 'child_process';
import { promises as fs } from 'fs';

import path from "path";
const router = express.Router();

// Import your weather data model
import user from "../models/user.js";
import WeatherData from "../models/WeatherData.js";
import Log from "../models/Log.js";

router.post('/generate-forecast', async (req, res) => {
  try {
    console.log('Starting forecast generation...');
    
    // Get last 10 days of weather data from MongoDB
    const tenDaysAgo = new Date();
    tenDaysAgo.setDate(tenDaysAgo.getDate() - 10);
    
    const historicalData = await WeatherData.find({
      date: { $gte: tenDaysAgo }
    }).sort({ date: 1 }).limit(10);
    
    if (historicalData.length < 10) {
      return res.status(400).json({ 
        error: 'Insufficient historical data. Need at least 10 days of records.' 
      });
    }
    
    // Prepare data for Python script
    const inputData = {
      historical_records: historicalData.map(record => ({
        date: record.date,
        weather_condition: record.weather_condition,
        temp_max: record.temp_max,
        temp_min: record.temp_min,
        humidity_max: record.humidity_max,
        humidity_min: record.humidity_min
      }))
    };
    
    // Create temporary input file
    const inputFile = path.join(__dirname, '../ml/temp_input.json');
    await fs.writeFile(inputFile, JSON.stringify(inputData, null, 2));
    
    // Execute Python prediction script
    const pythonScript = path.join(__dirname, '../ml/predict.py');
    const python = spawn('python3', [pythonScript, inputFile]);
    
    let result = '';
    let error = '';
    
    python.stdout.on('data', (data) => {
      result += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      error += data.toString();
    });
    
    python.on('close', async (code) => {
      try {
        // Clean up temp file
        await fs.unlink(inputFile).catch(() => {});
        
        if (code !== 0) {
          console.error('Python script error:', error);
          return res.status(500).json({ 
            error: 'Failed to generate forecast',
            details: error
          });
        }
        
        const predictions = JSON.parse(result);
        
        // Optionally save predictions to database for caching
        const forecastData = {
          generated_at: new Date(),
          base_date: new Date(),
          forecasts: predictions.forecasts,
          recommendations: predictions.recommendations
        };
        
        // You could save this to a Forecasts collection if needed
        // await Forecast.create(forecastData);
        
        // Log the forecast generation activity
        await Log.create({
          action: 'forecast_generated',
          user_id: req.user?.id || null, // If you have user authentication
          details: {
            forecasts_count: predictions.forecasts.length,
            recommendations_count: predictions.recommendations.length
          },
          timestamp: new Date()
        });
        
        res.json({
          success: true,
          data: forecastData
        });
        
      } catch (parseError) {
        console.error('Error parsing Python output:', parseError);
        console.error('Python output:', result);
        res.status(500).json({ 
          error: 'Failed to parse forecast results',
          details: result
        });
      }
    });
    
  } catch (error) {
    console.error('Forecast generation error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      details: error.message
    });
  }
});

// Get latest forecast
router.get('/latest', async (req, res) => {
  try {
    // This would get the latest forecast from database if you're caching them
    // For now, we'll return a message to generate new forecast
    res.json({
      message: 'Use POST /generate-forecast to create new predictions'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});


router.post('/recommendations', (req, res) => {
  const inputData = req.body.input_data;
  const lastDataDate = req.body.last_data_date || null;

  const python = spawn('python', ['ml/predict.py', JSON.stringify(inputData), lastDataDate]);

  let result = '';
  python.stdout.on('data', (data) => {
    result += data.toString();
  });

  python.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
  });

  python.on('close', (code) => {
    res.send(result);
  });
});

export default router;