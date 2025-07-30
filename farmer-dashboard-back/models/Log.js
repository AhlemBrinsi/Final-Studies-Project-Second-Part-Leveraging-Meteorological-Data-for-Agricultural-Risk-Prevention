import mongoose from 'mongoose';

const logSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'user' },
  username: String,
  eventType: String,
  eventCategory: String,
  description: String,
  ipAddress: String,
  severity: String,
  relatedEntity: String,
  timestamp: { type: Date, default: Date.now }
}, { timestamps: true });

const Log = mongoose.models.log || mongoose.model('Log', logSchema);
export default Log;
