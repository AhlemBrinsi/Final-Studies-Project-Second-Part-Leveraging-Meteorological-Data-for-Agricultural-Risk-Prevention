import express from "express";
const router = express.Router();
import Log from "../models/Log.js";

router.get('/', async (req, res) => {
  try {
    const { user, eventType, severity, startDate, endDate } = req.query;
    let { page = 1, limit = 20 } = req.query;

    page = parseInt(page) || 1;
    limit = parseInt(limit) || 20;

    const query = {};
    if (user) query.username = { $regex: user, $options: 'i' }; // partial, case-insensitive match
    if (eventType) query.eventType = eventType;
    if (severity) query.severity = severity;
    if (startDate || endDate) {
      query.timestamp = {};
      if (startDate) query.timestamp.$gte = new Date(startDate);
      if (endDate) query.timestamp.$lte = new Date(endDate);
    }

    console.log('Fetching logs with query:', query, 'page:', page, 'limit:', limit);

    const logs = await Log.find(query)
      .sort({ timestamp: -1 })
      .skip((page - 1) * limit)
      .limit(limit);

    const total = await Log.countDocuments(query);

    res.json({ logs, total, page, pages: Math.ceil(total / limit) });
  } catch (err) {
    console.error('Error fetching logs:', err);
    res.status(500).json({ error: 'Server error' });
  }
});

export default router;
