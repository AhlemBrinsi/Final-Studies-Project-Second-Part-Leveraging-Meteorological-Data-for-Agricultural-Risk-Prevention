import express from 'express';
const router = express.Router();
import User from '../models/user.js';
import Article from '../models/article.js';
import Feedback from'../models/Feedback.js';
import SupportTicket from '../models/supportTicket.js';
import Log from '../models/Log.js';
import supportTicket from '../models/supportTicket.js';

router.get('/summary', async (req, res) => {
  try {
    const [users, articles, feedbacks, supportTickets, logs] = await Promise.all([
      User.countDocuments(),
      Article.countDocuments(),
      Feedback.countDocuments(),
      SupportTicket.countDocuments(),
      Log.countDocuments()
    ]);

    res.json({ users, articles, feedbacks, supportTickets, logs });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch analytics summary' });
  }
});

// Articles per day for each month 
router.get('/articles-per-day', async (req, res) => {
  try {
    const result = await Article.aggregate([
      {
        $group: {
          _id: {
            month: { $month: '$createdAt' },
            day: { $dayOfMonth: '$createdAt' }
          },
          count: { $sum: 1 }
        }
      },
      { $sort: { '_id.month': 1, '_id.day': 1 } }
    ]);

    // Number of days per month (non-leap year)
    const daysInMonth = {
      1: 31,
      2: 28, // or 29 if you want to consider leap years approximately
      3: 31,
      4: 30,
      5: 31,
      6: 30,
      7: 31,
      8: 31,
      9: 30,
      10: 31,
      11: 30,
      12: 31,
    };

    // Initialize counts per day for each month
    const articlesPerDay = {};
    for (let m = 1; m <= 12; m++) {
      articlesPerDay[m] = Array(daysInMonth[m]).fill(0);
    }

    // Fill in counts from aggregation
    result.forEach(({ _id, count }) => {
      const { month, day } = _id;
      if (day <= daysInMonth[month]) {
        articlesPerDay[month][day - 1] = count; // zero-based index
      }
    });

    res.json({ articlesPerDay });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Error fetching articles per day for each month' });
  }
});

// Assuming Article schema has an owner
router.get('/articles-per-user', async (req, res) => {
  try {
    const result = await Article.aggregate([
      {
        $group: {
          _id: '$owner',  // or '$user' depending on your schema
          count: { $sum: 1 }
        }
      },
      {
        $lookup: {  // Optional: populate user info from User collection
          from: 'users',
          localField: '_id',
          foreignField: '_id',
          as: 'userInfo'
        }
      },
      {
        $unwind: '$userInfo'
      },
      {
        $project: {
          _id: 0,
          userId: '$_id',
          username: '$userInfo.username', // Or name or email etc
          count: 1
        }
      },
      {
        $sort: { count: -1 } // Sort descending by count
      }
    ]);

    res.json({ articlesPerUser: result });
  } catch (err) {
    res.status(500).json({ error: 'Error fetching articles per user' });
  }
});

// Signups per day for each  month

router.get('/signups-per-day', async (req, res) => {
  try {
    const result = await User.aggregate([
      {
        $group: {
          _id: {
            month: { $month: "$timestemp" },
            day: { $dayOfMonth: "$timestemp" },
          },
          count: { $sum: 1 }
        }
      },
      { $sort: { "_id.month": 1, "_id.day": 1 } }
    ]);

    const daysInMonth = {
      1: 31,
      2: 28, // ignore leap years for simplicity or adjust accordingly
      3: 31,
      4: 30,
      5: 31,
      6: 30,
      7: 31,
      8: 31,
      9: 30,
      10: 31,
      11: 30,
      12: 31,
    };

    // Initialize signups count per day for each month
    const signupsPerDay = {};
    for (let m = 1; m <= 12; m++) {
      signupsPerDay[m] = Array(daysInMonth[m]).fill(0);
    }

    // Fill in the aggregated counts
    result.forEach(({ _id, count }) => {
      const { month, day } = _id;
      if (day <= daysInMonth[month]) {
        signupsPerDay[month][day - 1] = count; // zero-based index
      }
    });

    res.json({ signupsPerDay });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch signups per day for each month" });
  }
});



// Feedbacks grouped by sentiment

router.get('/feedback-sentiment', async (req, res) => {
  try {
    const results = await Feedback.aggregate([
      {
        $group: {
          _id: "$sentiment.label",
          count: { $sum: 1 }
        }
      }
    ]);

    const response = { positive: 0, neutral: 0, negative: 0 };
    results.forEach(item => {
      response[item._id] = item.count;
    });

    res.json(response);
  } catch (err) {
    console.error("Aggregation error:", err);
    res.status(500).json({ error: "Failed to fetch sentiment data" });
  }
});
// Logs over time

router.get('/logs-over-time', async (req, res) => {
  try {
    const logs = await Log.aggregate([
      {
        $group: {
          _id: {
            $dateToString: { format: "%Y-%m-%d", date: "$timestamp" }
          },
          count: { $sum: 1 }
        }
      },
      { $sort: { _id: 1 } }
    ]);

    const labels = logs.map(log => log._id);
    const counts = logs.map(log => log.count);

    res.json({ labels, counts });
  } catch (err) {
    res.status(500).json({ message: 'Error fetching logs over time', error: err });
  }
});

// Logs grouped by event

router.get('/logs-by-event-type', async (req, res) => {
  try {
    const logs = await Log.aggregate([
      {
        $group: {
          _id: '$eventType',
          count: { $sum: 1 }
        }
      },
      { $sort: { count: -1 } }
    ]);

    const labels = logs.map(log => log._id);
    const counts = logs.map(log => log.count);

    res.json({ labels, counts });
  } catch (err) {
    res.status(500).json({ message: 'Error fetching logs by event type', error: err });
  }
});


// GET /api/analytics/support/status-counts
router.get('/status-counts', async (req, res) => {
  try {
    // Aggregate tickets by status and count
    const counts = await SupportTicket.aggregate([
      {
        $group: {
          _id: "$status",
          count: { $sum: 1 }
        }
      }
    ]);

    // Prepare response object with default 0 counts
    const response = {
      open: 0,
      closed: 0,
    };

    // Fill in counts from aggregation
    counts.forEach(item => {
      if (item._id === 'open') response.open = item.count;
      else if (item._id === 'closed') response.closed = item.count;
    });

    res.json(response);
  } catch (err) {
    console.error('Error fetching support ticket status counts:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});
// 👤 3. Tickets by User
router.get('/tickets-by-user', async (req, res) => {
  try {
    const data = await SupportTicket.aggregate([
      {
        $group: {
          _id: "$owner",
          count: { $sum: 1 }
        }
      },
      {
        $lookup: {
          from: 'users',
          localField: '_id',
          foreignField: '_id',
          as: 'user'
        }
      },
      {
        $unwind: "$user"
      },
      {
        $project: {
          _id: 0,
          username: "$user.username",
          count: 1
        }
      },
      {
        $sort: { count: -1 }
      }
    ]);
    res.json(data);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

export default router;
