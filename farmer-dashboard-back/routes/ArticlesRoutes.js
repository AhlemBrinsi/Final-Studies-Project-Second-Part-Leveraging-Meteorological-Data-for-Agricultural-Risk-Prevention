import express from 'express';
import article from '../models/article.js';
import Feedback from '../models/Feedback.js';
import { verifyToken } from '../middleware/auth.js';


const router = express.Router();


router.post('/', verifyToken, async (req, res) => {
  try {
    const newArticle = new article({ ...req.body, owner: req.userId });
    await newArticle.save();
    res.status(201).json(newArticle);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});


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


// Post feedback on an article (requires auth)
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
    res.status(201).json(feedback);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});

// Delete an article (requires auth)
router.delete('/:id', verifyToken, async (req, res) => {
  try {
    const foundArticle = await article.findById(req.params.id);
    if (!foundArticle) return res.status(404).json({ message: "Article not found" });

    if (foundArticle.owner.toString() !== req.userId) {
      return res.status(403).json({ message: "Not authorized to delete this article" });
    }

    await foundArticle.deleteOne();
    res.json({ message: "Article deleted successfully" });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// DELETE /api/articles/:articleId/feedbacks/:feedbackId
router.delete('/:articleId/feedbacks/:feedbackId', verifyToken, async (req, res) => {
  const { articleId, feedbackId } = req.params;
  try {
    const feedback = await Feedback.findById(feedbackId);
    if (!feedback) return res.status(404).json({ message: 'Feedback not found' });

    if (feedback.article.toString() !== articleId) {
      return res.status(400).json({ message: 'Feedback does not belong to this article' });
    }

    if (feedback.owner.toString() !== req.userId) {  // ici owner au lieu de user
      return res.status(403).json({ message: 'Not authorized to delete this feedback' });
    }

    await feedback.deleteOne();
    res.status(200).json({ message: 'Feedback deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error });
  }
});




export default router;
