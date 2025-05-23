import mongoose from 'mongoose';

const feedbackSchema = new mongoose.Schema({
  article: { type: mongoose.Schema.Types.ObjectId, ref: 'Article' },
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'user',required: true },
  comment: String,
  rating: Number
}, { timestamps: true });

export default mongoose.model('Feedback', feedbackSchema);
