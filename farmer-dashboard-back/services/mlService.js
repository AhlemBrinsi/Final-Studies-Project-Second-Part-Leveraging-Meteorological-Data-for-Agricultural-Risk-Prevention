const axios = require('axios');

class MLService {
    constructor() {
        // For development, use localhost. For production, use your deployed ML service URL
        this.baseURL = process.env.ML_SERVICE_URL || 'http://localhost:5000';
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: 30000, // 30 seconds timeout for ML processing
        });
    }

    async getPredictions(weatherData) {
        try {
            const response = await this.client.post('/predict', {
                weather_data: weatherData
            });
            return response.data;
        } catch (error) {
            console.error('ML Service Error:', error.message);
            throw new Error('Failed to get predictions from ML service');
        }
    }

    async getRecommendations(weatherData) {
        try {
            const response = await this.client.post('/recommendations', {
                weather_data: weatherData
            });
            return response.data;
        } catch (error) {
            console.error('ML Service Error:', error.message);
            throw new Error('Failed to get recommendations from ML service');
        }
    }
}

module.exports = new MLService();