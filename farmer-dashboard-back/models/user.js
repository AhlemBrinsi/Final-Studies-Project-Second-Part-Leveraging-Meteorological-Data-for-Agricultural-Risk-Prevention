import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  username: { type: String, unique: true },  
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, required: true },
  verified: { type: Boolean, default: false },
  resetToken: { type: String },
  resetTokenExpires: { type: Date },
  job: { type: String, default: ""},
  bio: { type: String, default: "" },
  profilePicture: { type: String, default: "" }, 
  age: {type: Number}
}, { timestamps: true });

const user = mongoose.models.user || mongoose.model('user', userSchema);
export default user;
