import express from "express";
const router = express.Router();

import user from "../models/user.js";
import WeatherData from "../models/WeatherData.js";
import Log from "../models/Log.js";
// GET /api/weather - Get all weather data with pagination
router.get('/', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;

    const weatherData = await WeatherData.find()
      .sort({ date: -1 })
      .skip(skip)
      .limit(limit);

    const total = await WeatherData.countDocuments();

    res.json({
      success: true,
      data: weatherData,
      pagination: {
        currentPage: page,
        totalPages: Math.ceil(total / limit),
        totalRecords: total,
        hasNext: page < Math.ceil(total / limit),
        hasPrev: page > 1
      }
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// GET /api/weather/:id - Get specific weather record
router.get('/:id', async (req, res) => {
  try {
    const weatherData = await WeatherData.findById(req.params.id);
    
    if (!weatherData) {
      return res.status(404).json({ 
        success: false, 
        error: 'Weather record not found' 
      });
    }

    res.json({
      success: true,
      data: weatherData
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// POST /api/weather - Add new weather data
router.post('/', async (req, res) => {
  try {
    const {
      date,
      weather_condition,
      temp_max,
      temp_min,
      humidity_max,
      humidity_min,
      location
    } = req.body;

    // Validation
    if (!date || !weather_condition || temp_max === undefined || 
        temp_min === undefined || humidity_max === undefined || 
        humidity_min === undefined) {
      return res.status(400).json({
        success: false,
        error: 'All weather fields are required'
      });
    }

    const weatherData = new WeatherData({
      date: new Date(date),
      weather_condition,
      temp_max,
      temp_min,
      humidity_max,
      humidity_min,
      location: location || 'Default Location',
      created_by: req.user?.id || null
    });

    await weatherData.save();

    // Log the activity
    await Log.create({
      action: 'weather_data_added',
      user_id: req.user?.id || null,
      details: {
        date: weatherData.date,
        weather_condition: weatherData.weather_condition
      },
      timestamp: new Date()
    });

    res.status(201).json({
      success: true,
      data: weatherData,
      message: 'Weather data added successfully'
    });
  } catch (error) {
    if (error.code === 11000) {
      return res.status(400).json({
        success: false,
        error: 'Weather data for this date already exists'
      });
    }
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// PUT /api/weather/:id - Update weather data
router.put('/:id', async (req, res) => {
  try {
    const weatherData = await WeatherData.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    );

    if (!weatherData) {
      return res.status(404).json({ 
        success: false, 
        error: 'Weather record not found' 
      });
    }

    // Log the activity
    await Log.create({
      action: 'weather_data_updated',
      user_id: req.user?.id || null,
      details: {
        weather_id: weatherData._id,
        date: weatherData.date
      },
      timestamp: new Date()
    });

    res.json({
      success: true,
      data: weatherData,
      message: 'Weather data updated successfully'
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// DELETE /api/weather/:id - Delete weather data
router.delete('/:id', async (req, res) => {
  try {
    const weatherData = await WeatherData.findByIdAndDelete(req.params.id);

    if (!weatherData) {
      return res.status(404).json({ 
        success: false, 
        error: 'Weather record not found' 
      });
    }

    // Log the activity
    await Log.create({
      action: 'weather_data_deleted',
      user_id: req.user?.id || null,
      details: {
        weather_id: req.params.id,
        date: weatherData.date
      },
      timestamp: new Date()
    });

    res.json({
      success: true,
      message: 'Weather data deleted successfully'
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// GET /api/weather/recent/:days - Get recent weather data
router.get('/recent/:days', async (req, res) => {
  try {
    const days = parseInt(req.params.days) || 7;
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const weatherData = await WeatherData.find({
      date: { $gte: startDate }
    }).sort({ date: -1 });

    res.json({
      success: true,
      data: weatherData,
      count: weatherData.length
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

export default router;