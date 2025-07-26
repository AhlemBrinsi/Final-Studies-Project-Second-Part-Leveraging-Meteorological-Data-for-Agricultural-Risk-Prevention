import mongoose from 'mongoose';

const weatherDataSchema = new mongoose.Schema({
  date: {
    type: Date,
    required: true,
    unique: true
  },
  weather_condition: {
    type: String,
    required: true
  },
  temp_max: {
    type: Number,
    required: true,
    min: -50,
    max: 60
  },
  temp_min: {
    type: Number,
    required: true,
    min: -50,
    max: 60
  },
  humidity_max: {
    type: Number,
    required: true,
    min: 0,
    max: 100
  },
  humidity_min: {
    type: Number,
    required: true,
    min: 0,
    max: 100
  },
  location: {
    type: String,
    default: 'Default Location'
  },
  created_by: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'user',
    required: false // Admin can add weather data
  }
}, {
  timestamps: true
});

// Index for efficient querying by date
weatherDataSchema.index({ date: -1 });

// Validation: temp_min should be <= temp_max
weatherDataSchema.pre('save', function(next) {
  if (this.temp_min > this.temp_max) {
    next(new Error('Minimum temperature cannot be higher than maximum temperature'));
  }
  if (this.humidity_min > this.humidity_max) {
    next(new Error('Minimum humidity cannot be higher than maximum humidity'));
  }
  next();
});

export default mongoose.model('WeatherData', weatherDataSchema);