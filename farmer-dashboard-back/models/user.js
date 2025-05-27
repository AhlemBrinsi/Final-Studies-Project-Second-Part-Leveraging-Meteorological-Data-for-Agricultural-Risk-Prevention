import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  username: { type: String, unique: true },  // add this
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, required: true },
  verified: { type: Boolean, default: false },
  resetToken: { type: String },
  resetTokenExpires: { type: Date },
  job: { type: String, default: ""},
  bio: { type: String, default: "" },
  profilePicture: { type: String, default: "" }, // store URL or filename/path
  age: {type: Number}
}, { timestamps: true });

export default mongoose.model('user', userSchema); 