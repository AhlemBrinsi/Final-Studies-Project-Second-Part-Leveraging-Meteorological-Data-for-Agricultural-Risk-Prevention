import express from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import User from "../models/user.js";

const router = express.Router();

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


// GET user profile by ID
/*router.get("/:_id", async (req, res) => {
  try {
    const user = await User.findById(req.params._id);
    if (!user) return res.status(404).send("User not found");
    res.json(user);
  } catch (err) {
    res.status(500).json({ message: "Error fetching profile", error: err.message });
  }
});

router.put('/:_id', upload.single('profilePicture'), async (req, res) => {
  try {
    const userId = req.params._id;
    const updateData = {
      username: req.body.username,
      email: req.body.email,
      position: req.body.position,
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
});*/

export default router;
