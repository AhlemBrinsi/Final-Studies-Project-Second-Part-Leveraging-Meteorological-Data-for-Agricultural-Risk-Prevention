import mongoose from 'mongoose';

const feedbackSchema = new mongoose.Schema({
  article: { type: mongoose.Schema.Types.ObjectId, ref: 'Article' },
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'user',required: true },
  comment: String,
  rating: Number,
  sentiment: {
    score: Number,    // sentiment score (e.g. -5 to +5)
    comparative: Number,  // normalized score
    label: { type: String, enum: ['positive', 'neutral', 'negative'] },
  }
}, { timestamps: true });

export default mongoose.model('Feedback', feedbackSchema);
