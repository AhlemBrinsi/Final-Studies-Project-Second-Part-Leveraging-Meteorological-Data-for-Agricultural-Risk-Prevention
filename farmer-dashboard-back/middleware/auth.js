import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';

dotenv.config(); // Load .env variables

export const verifyToken = (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1]; // Bearer <token>
    if (!token) return res.status(401).json({ message: 'Access Denied. No token provided.' });

    const decoded = jwt.verify(token, process.env.JWT_SECRET); // Use .env secret
    req.userId = decoded.id; // Set userId for routes
    next();
  } catch (err) {
    res.status(401).json({ message: 'Invalid Token' });
  }
};
