import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';

dotenv.config(); // Load .env variables

export const verifyToken = (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1]; // Bearer <token>
    if (!token) return res.status(401).json({ message: 'Access Denied. No token provided.' });

    const decoded = jwt.verify(token, process.env.JWT_SECRET); 
    req.user = {
      _id: decoded.id,
      username: decoded.username,
      role: decoded.role,

    };
    req.userId = decoded.id; // Set userId for routes
    next();
  } catch (err) {
    res.status(401).json({ message: 'Invalid Token' });
  }
};



/*
import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';

dotenv.config();

const JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret_here';

// Middleware to verify token and extract user info
export const verifyToken = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization; // Expected format: 'Bearer <token>'
    if (!authHeader) return res.status(401).json({ message: 'Access Denied. No token provided.' });

    const token = authHeader.split(' ')[1];
    if (!token) return res.status(401).json({ message: 'Access Denied. No token provided.' });

    const decoded = jwt.verify(token, JWT_SECRET);

    // Attach user info to req
    req.user = {
      _id: decoded.id,
      username: decoded.username,
    };
    req.userId = decoded.id;

    next();
  } catch (err) {
    res.status(401).json({ message: 'Invalid Token' });
  }
};
*/