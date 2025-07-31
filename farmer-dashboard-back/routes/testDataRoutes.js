import express from 'express';
import { getDB } from '../db.js';  // Your DB connection helper

const router = express.Router();

router.get('/test-data-last-week', async (req, res) => {
  try {
    const db = await getDB();
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    const startDateStr = oneWeekAgo.toISOString().slice(0, 10);
    const fetchAll = req.query.all === 'true';
    const query = fetchAll ? {} : { date: { $gte: startDateStr } };

    const data = await db.collection('test_data')
      .find(query)
      .sort({ date: 1 }) // already sorted by ascending date
      .toArray();

    res.json(data.slice(-10)); // ✅ return last 10 records
  } catch (error) {
    console.error('Error fetching last week test data:', error);
    res.status(500).json({ message: 'Server error' });
  }
});


export default router;
