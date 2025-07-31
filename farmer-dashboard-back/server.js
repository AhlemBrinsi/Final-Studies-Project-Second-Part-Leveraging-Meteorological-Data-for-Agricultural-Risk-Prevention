import express from 'express';
import mongoose from 'mongoose';
import articlesRoutes from './routes/ArticlesRoutes.js';
import userRoutes from './routes/userRoutes.js';
import uploadRoutes from './routes/uploadRoutes.js'; 
import supportRoutes from "./routes/supportRoutes.js";
import LogsRoutes from "./routes/LogsRoutes.js"
import AnalyticsRoutes from './routes/AnalyticsRoutes.js';
import weatherRoutes from './routes/weatherRoutes.js';
import recommendationRoutes from './routes/recommendationRoutes.js'; 
import testDataRoutes from './routes/testDataRoutes.js';

import path from 'path';
import cors from 'cors';
import dotenv from 'dotenv';
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use('/uploads', express.static(path.resolve('uploads')));
app.use('/api/articles', articlesRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/users', userRoutes);
app.use("/api/support", supportRoutes);
app.use("/api/logs", LogsRoutes);
app.use('/api/analytics', AnalyticsRoutes);
app.use('/api/weather', weatherRoutes); 
app.use('/api/recommendations', recommendationRoutes); 
app.use('/api', testDataRoutes); 
//app.use("/api/profile", profileRoutes);


// Connect to DB
//mongoose.connect(process.env.MONGO_URL, {
 // useNewUrlParser: true,
 // useUnifiedTopology: true,
//})
//.then(() => console.log("MongoDB connected"))
//.catch((err) => console.error(err));


mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('Connected to MongoDB Atlas'))
.catch(err => console.error('MongoDB connection error:', err));


// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
