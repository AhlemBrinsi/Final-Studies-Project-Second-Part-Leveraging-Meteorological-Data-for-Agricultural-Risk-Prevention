import mongoose from "mongoose";

const SupportTicketSchema = new mongoose.Schema({
  subject: { type: String, required: true, trim: true },
  message: { type: String, required: true },
  response: { type: String, default: "" },
  status: { type: String, enum: ["open", "closed"], default: "open" },
  createdAt: { type: Date, default: Date.now },
  respondedAt: { type: Date },
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'user', required: true },
}, { timestamps: true });

export default mongoose.model("SupportTicket", SupportTicketSchema);
