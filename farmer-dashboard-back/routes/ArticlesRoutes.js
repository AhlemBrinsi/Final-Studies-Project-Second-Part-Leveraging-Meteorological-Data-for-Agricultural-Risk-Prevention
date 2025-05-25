import express from 'express';
import article from '../models/article.js';
import Feedback from '../models/Feedback.js';
import { verifyToken } from '../middleware/auth.js';
import { createLog } from '../controllers/logger.js';
import User from '../models/user.js';
const router = express.Router();

// Create an article 
router.post('/', verifyToken, async (req, res) => {
  try {
    const newArticle = new article({ ...req.body, owner: req.userId });
    await newArticle.save();

    // Saving Log
    try {
      const user = await User.findById(req.userId);
      if (!user) throw new Error('User not found');
      await createLog({
        userId: req.userId, 
        username: req.user.username,
        eventType: 'ARTICLE_CREATE',
        eventCategory: 'Article',
        description: `Article "${newArticle.title}" created`,
        ipAddress: req.ip,
        severity: 'INFO',
        relatedEntity: `Article:${newArticle._id}`,
      });
    } catch (logErr) {
      console.error('Error in creating log :', logErr);
    }

    res.status(201).json(newArticle);
  } catch (err) {
    console.error('Error in creating Article :', err);
    res.status(400).json({ message: err.message });
  }
});

// Add a feedback on an article

router.post('/:id/feedback', verifyToken, async (req, res) => {
  try {
    const { comment, rating } = req.body;
    const feedback = new Feedback({
      article: req.params.id,
      owner: req.userId, // ici owner au lieu de user
      comment,
      rating
    });
    await feedback.save();
    try {
      const user = await User.findById(req.userId);
      if (!user) throw new Error('User not found');
      await createLog({
        userId: req.userId, 
        username: req.user.username,
        eventType: 'FEEDBACK_CREATE',
        eventCategory: 'Feedback',
        description: "Feedback created",
        ipAddress: req.ip,
        severity: 'INFO',
        relatedEntity: `Article:${feedback._id}`,
      });
    } catch (logErr) {
      console.error('Error in creating log :', logErr);
    }
    res.status(201).json(feedback);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});

// Get the article with his feedbacks to be displayed on the dashboard
router.get('/', async (req, res) => {
  try {
    const articles = await article.find()
      .populate('owner', 'username')
      .lean();

    const feedbacks = await Feedback.find()
      .populate('owner', 'username')
      .lean();

    const articlesWithFeedbacks = articles.map(a => {
      a.feedbacks = feedbacks.filter(fb => fb.article.toString() === a._id.toString());
      return a;
    });

    res.json(articlesWithFeedbacks);
  } catch (err) {
    res.status(500).json({ message: 'Failed to fetch articles and feedbacks' });
  }
});

// delete article
router.delete('/:id', verifyToken, async (req, res) => {
  try {
    const foundArticle = await article.findById(req.params.id);
    if (!foundArticle) return res.status(404).json({ message: "Article not found" });

    if (foundArticle.owner.toString() !== req.userId) {
      return res.status(403).json({ message: "Not authorized to delete this article" });
    }

    // Delete all feedbacks associated with this article
    await Feedback.deleteMany({ article: foundArticle._id });

    // Then delete the article
    await foundArticle.deleteOne();

    try {
      const user = await User.findById(req.userId);
      if (!user) throw new Error('User not found');
      await createLog({
        userId: req.userId, 
        username: req.user.username,
        eventType: 'ARTICLE_DELETE',
        eventCategory: 'Article',
        description: `Article "${foundArticle.title}" deleted `,
        ipAddress: req.ip,
        severity: 'INFO',
        relatedEntity: `Article:${foundArticle._id}`,
      });
    } catch (logErr) {
      console.error('Error in creating log :', logErr);
    }

    res.json({ message: "Article and its feedbacks deleted successfully" });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// Update Article
router.put('/:id', verifyToken, async (req, res) => {
  try {
    const foundArticle = await article.findById(req.params.id);
    if (!foundArticle) return res.status(404).json({ message: 'Article not found' });

    if (foundArticle.owner.toString() !== req.userId) {
      return res.status(403).json({ message: 'Not authorized to update this article' });
    }

    Object.assign(foundArticle, req.body);
    await foundArticle.save();
    try {
      const user = await User.findById(req.userId);
      if (!user) throw new Error('User not found');
      await createLog({
        userId: req.userId, 
        username: req.user.username,
        eventType: 'ARTICLE_EDIT',
        eventCategory: 'Article',
        description: `Article "${foundArticle.title}" edited`,
        ipAddress: req.ip,
        severity: 'INFO',
        relatedEntity: `Article:${foundArticle._id}`,
      });
    } catch (logErr) {
      console.error('Error in creating log :', logErr);
    }

    res.json({ message: 'Article updated successfully', article: foundArticle });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// Delete feedback
router.delete('/:articleId/feedbacks/:feedbackId', verifyToken, async (req, res) => {
  const { articleId, feedbackId } = req.params;
  try {
    const feedback = await Feedback.findById(feedbackId);
    if (!feedback) return res.status(404).json({ message: 'Feedback not found' });

    if (feedback.article.toString() !== articleId) {
      return res.status(400).json({ message: 'Feedback does not belong to this article' });
    }

    if (feedback.owner.toString() !== req.userId) { 
      return res.status(403).json({ message: 'Not authorized to delete this feedback' });
    }

    await feedback.deleteOne();
    try {
      const user = await User.findById(req.userId);
      if (!user) throw new Error('User not found');
      await createLog({
        userId: req.userId, 
        username: req.user.username,
        eventType: 'FEEDBACK_DELETE',
        eventCategory: 'Feedback',
        description: `Feedback "${feedback.title}" deleted`,
        ipAddress: req.ip,
        severity: 'INFO',
        relatedEntity: `Feedback:${feedback._id}`,
      });
    } catch (logErr) {
      console.error('Error in creating log :', logErr);
    }
    res.status(200).json({ message: 'Feedback deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error });
  }
});

// Update feedback
router.put('/:articleId/feedbacks/:feedbackId', verifyToken, async (req, res) => {
  const { comment, rating } = req.body;
  const { articleId, feedbackId } = req.params;
  try {
    // Check if the feedback exists and belongs to the article
    const feedback = await Feedback.findById(feedbackId);
    if (!feedback) return res.status(404).json({ message: 'Feedback not found' });
    if (feedback.article.toString() !== articleId) {
      return res.status(400).json({ message: 'Feedback does not belong to this article' });
    }
    // Check if the user owns this feedback
    if (feedback.owner.toString() !== req.userId) {
      return res.status(403).json({ message: 'Not authorized to update this feedback' });
    }

    // Update fields
    feedback.comment = comment;
    feedback.rating = rating;
    await feedback.save();

    try {
      const user = await User.findById(req.userId);
      if (!user) throw new Error('User not found');
      await createLog({
        userId: req.userId, 
        username: req.user.username,
        eventType: 'FEEDBACK_EDIT',
        eventCategory: 'Feedback',
        description: `Feedback "${feedback.title}" edited`,
        ipAddress: req.ip,
        severity: 'INFO',
        relatedEntity: `Feedback:${feedback._id}`,
      });
    } catch (logErr) {
      console.error('Error in creating log :', logErr);
    }
    res.status(200).json({ message: 'Feedback updated successfully', feedback });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Server error', error });
  }
});

export default router;
