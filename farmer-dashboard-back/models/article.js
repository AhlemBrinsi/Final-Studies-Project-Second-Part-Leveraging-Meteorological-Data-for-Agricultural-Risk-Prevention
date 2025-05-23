import mongoose from 'mongoose';

const articleSchema = new mongoose.Schema({
  title: { type: String, required: true },
  authorName: { type: String, required: true }, // Name of the real author
  publishedDate: { type: Date, required: true }, // Date the article was originally published
  sourceName: { type: String, required: true }, // Name of the book or research paper
  content: { type: String, required: true },
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'user', required: true },
}, { timestamps: true });

export default mongoose.model('article', articleSchema);
