import express from 'express';
import mongoose from 'mongoose';
import User from './models/user.js'; 
import path from 'path';

import cors from 'cors';

import userRoutes from './routes/userRoutes.js';
import profileRoutes from "./routes/profile.js";

import dotenv from 'dotenv';
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use('/api/users', userRoutes);
//app.use("/api/profile", profileRoutes);

// Connect to DB
mongoose.connect(process.env.MONGO_URL, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log("MongoDB connected"))
.catch((err) => console.error(err));
app.use('/uploads', express.static(path.resolve('uploads')));

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
