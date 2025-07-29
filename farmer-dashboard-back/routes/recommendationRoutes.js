import express from 'express';
import { getDB } from '../db.js'; 

const router = express.Router();

router.get('/', async (req, res) => {
  try {
    const db = await getDB();
    const recommendationData = await db.collection('recommendations').find().sort({ _id: -1 }).limit(1).toArray();
    res.json(recommendationData[0]);
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

export default router;
