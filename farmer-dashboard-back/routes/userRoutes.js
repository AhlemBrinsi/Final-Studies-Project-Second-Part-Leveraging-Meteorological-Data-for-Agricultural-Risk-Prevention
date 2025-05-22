import express from 'express';
import User from '../models/user.js';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import nodemailer from 'nodemailer';
import dotenv from 'dotenv';
import crypto from 'crypto';
import path from "path";
import fs from "fs";
import multer from "multer";
import mongoose from 'mongoose';
dotenv.config(); // Load .env file

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET;


// Ensure upload directory exists
const uploadDir = path.resolve('uploads/profile-pics');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Multer storage setup
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${req.params._id}-${Date.now()}${ext}`);
  },
});
const upload = multer({ storage });


// Email transporter setup
const transporter = nodemailer.createTransport({
  service: 'Gmail',
  auth: {
    user: process.env.EMAIL_USER,      // Add to .env
    pass: process.env.EMAIL_PASS,      // Add to .env (use app password, not your Gmail password!)
  },
});

// Add user (register with email verification)
router.post('/register', async (req, res) => {
  const { username, email, password, role, ownerCode } = req.body;

  console.log("📥 Incoming registration:", { username, email, password, role, ownerCode });

  try {
    // Check if username or email already exists
    const existingUser = await User.findOne({
      $or: [{ email }, { username }]
    });
    if (existingUser) {
      return res.status(400).json({ message: 'User with this email or username already exists' });
    }

    // If role is "owner", validate the provided code
    if (role === 'owner') {
      const validCode = process.env.OWNER_CODE;

      console.log("🛠 ownerCode from client:", ownerCode);
      console.log("🔒 expected OWNER_CODE from env:", validCode);

      if (!ownerCode || ownerCode.trim() !== validCode?.trim()) {
        return res.status(403).json({ message: 'Invalid owner code' });
      }
    }


    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = new User({ username, email, password: hashedPassword, role, verified: false });
    await newUser.save();

    const token = jwt.sign({ email }, JWT_SECRET, { expiresIn: '1h' });
    const verificationUrl = `http://localhost:5000/api/users/verify-email?token=${token}`;

    await transporter.sendMail({
      from: process.env.EMAIL_USER,
      to: email,
      subject: 'Verify your email',
      html: `<p>Click <a href="${verificationUrl}">here</a> to verify your email.</p>`
    });

    res.status(201).json({ message: 'User registered. Verification email sent.' });
  } catch (err) {
    console.error("❌ Error in /register route:", err);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


// Email verification route
router.get('/verify-email', async (req, res) => {
  try {
    const { token } = req.query;
    const decoded = jwt.verify(token, JWT_SECRET);

    const user = await User.findOne({ email: decoded.email });
    if (!user) return res.status(404).send('User not found');

    user.verified = true;
    await user.save();

    res.send('Email verified successfully! You can now login.');
  } catch (err) {
    res.status(400).send('Invalid or expired token');
  }
});

// Login route
router.post('/login', async (req, res) => {
  console.log('req.body:', req.body);
  const { emailOrUsername, password } = req.body;  // changed here

  try {
    const user = await User.findOne({
      $or: [
        { email: emailOrUsername },
        { username: emailOrUsername }
      ]
    });
    if (!user) return res.status(400).json({ message: 'User not found' });

    if (!user.verified) return res.status(403).json({ message: 'Email not verified' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(401).json({ message: 'Invalid credentials' });

    res.status(200).json({
      message: 'Login successful',
      user: { id: user._id, email: user.email, role: user.role, username: user.username },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});



// Request password reset
router.post('/forgot-password', async (req, res) => {
  const { email } = req.body;

  try {
    const user = await User.findOne({ email });
    if (!user) return res.status(404).json({ message: 'User not found' });

    const token = crypto.randomBytes(32).toString('hex');
    const resetLink = `http://localhost:5173/reset-password/${token}`;

    user.resetToken = token;
    user.resetTokenExpires = Date.now() + 3600000; // 1 hour
    await user.save();

    await transporter.sendMail({
      from: process.env.EMAIL_USER,
      to: email,
      subject: 'Reset your password',
      html: `<p>Click <a href="${resetLink}">here</a> to reset your password. This link expires in 1 hour.</p>`
    });

    res.json({ message: 'Reset password link sent to email' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});


// Reset password
router.post('/reset-password/:token', async (req, res) => {
  const { token } = req.params;
  const { newPassword } = req.body;

  try {
    const user = await User.findOne({
      resetToken: token,
      resetTokenExpires: { $gt: Date.now() },
    });

    if (!user) return res.status(400).json({ message: 'Invalid or expired token' });

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    user.password = hashedPassword;
    user.resetToken = undefined;
    user.resetTokenExpires = undefined;

    await user.save();

    res.json({ message: 'Password has been reset successfully' });
  } catch (err) {
    res.status(500).json({ error: 'Internal server error' });
  }
});



router.get("/:_id", async (req, res) => {
  try {
    if (!mongoose.Types.ObjectId.isValid(req.params._id)) {
      return res.status(400).json({ message: "Invalid user ID format" });
    }
    
    const user = await User.findById(req.params._id);
    if (!user) {
      return res.status(404).send("User not found");
    }
    
    res.json(user);
  } catch (err) {
    console.error("Error details:", err); // More detailed error logging
    res.status(500).json({ 
      message: "Error fetching profile", 
      error: err.message,
      receivedId: req.params._id // Include the received ID in the response
    });
  }
});



// Update user data by ID
router.put('/:_id', upload.single('profilePicture'), async (req, res) => {
  try {
    const userId = req.params._id;
    const updateData = {
      username: req.body.username,
      email: req.body.email,
      age: req.body.age,
      job: req.body.job,
      bio: req.body.bio,
    };

    // Handle uploaded file if present
    if (req.file) {
      updateData.profilePicture = `/uploads/profile-pics/${req.file.filename}`;
    }

    // Find user and update
    const user = await User.findByIdAndUpdate(userId, updateData, { new: true });
    if (!user) return res.status(404).json({ message: 'User not found' });

    res.json({
      message: 'Profile updated successfully',
      user,
    });
  } catch (error) {
    console.error('Error updating profile:', error);
    res.status(500).json({ message: 'Failed to update profile', error: error.message });
  }
});

export default router;
