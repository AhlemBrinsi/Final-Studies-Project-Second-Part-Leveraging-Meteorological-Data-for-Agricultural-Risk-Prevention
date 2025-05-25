import express from "express";
import SupportTicket from "../models/supportTicket.js";
import { verifyToken } from "../middleware/auth.js";
import { createLog } from '../controllers/logger.js';
import User from '../models/user.js'
const router = express.Router();

// GET /api/support - Get all support tickets
router.get("/", async (req, res) => {
  try {
    const tickets = await SupportTicket.find()
  .populate('owner', 'username') // populate the owner field but only with the username field
  .sort({ createdAt: -1 });
    res.json(tickets);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch support tickets." });
  }
});

// GET /api/support/:id - Get one ticket by ID
router.get("/:id", async (req, res) => {
  try {
    const ticket = await SupportTicket.findById(req.params.id);
    if (!ticket) return res.status(404).json({ error: "Ticket not found." });
    res.json(ticket);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch ticket." });
  }
});

// PATCH /api/support/:id - Update ticket (add response or change status)
router.patch("/:id",verifyToken, async (req, res) => {
  try {
    const { response, status } = req.body;
    const updateFields = {
      ...(response && { response }),
      ...(status && { status }),
      ...(response && { respondedAt: new Date() }),
    };

    const updatedTicket = await SupportTicket.findByIdAndUpdate(
      req.params.id,
      updateFields,
      { new: true }
    );

    // if (!updatedTicket) return res.status(404).json({ error: "Ticket not found." });
    try {
          const user = await User.findById(req.userId);
          if (!user) throw new Error('User not found');
          await createLog({
            userId: req.userId, 
            username: req.user.username,
            eventType: 'SUPPORT_EDIT',
            eventCategory: 'Support',
            description: `Support ticket "${updatedTicket.title}" edited`,
            ipAddress: req.ip,
            severity: 'INFO',
            relatedEntity: `Support ticket:${updatedTicket._id}`,
          });
        } catch (logErr) {
          console.error('Error in creating log :', logErr);
        }
    res.json(updatedTicket);
  } catch (err) {
    res.status(500).json({ error: "Failed to update ticket." });
  }
});

/*router.patch("/:id", verifyToken, async (req, res) => {
  try {
    const { response, status } = req.body;
    const ticketId = req.params.id;

    const updateFields = {
      ...(response && { response }),
      ...(status && { status }),
      ...(response && { respondedAt: new Date() }),
    };

    const updatedTicket = await SupportTicket.findByIdAndUpdate(
      ticketId,
      updateFields,
      { new: true }
    );

    if (!updatedTicket) return res.status(404).json({ error: "Ticket not found." });

    

    res.json(updatedTicket);
  } catch (err) {
    res.status(500).json({ error: "Failed to update ticket." });
  }
});*/



// POST /api/support - create new ticket
router.post("/",verifyToken,  async (req, res) => {
  try {
    const { owner, subject, message } = req.body;

    if (!owner || !subject || !message) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    const newTicket = new SupportTicket({
      owner,
      subject,
      message,
      status: "open",
    });

    const saved = await newTicket.save();
    try {
          const user = await User.findById(req.userId);
          if (!user) throw new Error('User not found');
          await createLog({
            userId: req.userId, 
            username: req.user.username,
            eventType: 'SUPPORT_CREATE',
            eventCategory: 'Support',
            description: `Support ticket "${saved.title}" created`,
            ipAddress: req.ip,
            severity: 'INFO',
            relatedEntity: `Support ticket :${saved._id}`,
          });
        } catch (logErr) {
          console.error('Error in creating log :', logErr);
        }
    res.status(201).json(saved);
  } catch (err) {
    console.error("Error creating ticket:", err); // Important!
    res.status(500).json({ error: "Server error creating ticket" });
  }
});

/*router.post("/", async (req, res) => {
  try {
    const { owner, subject, message } = req.body;

    if (!owner || !subject || !message) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    const newTicket = new SupportTicket({
      owner,
      subject,
      message,
      status: "open",
    });

    const saved = await newTicket.save();

    

    res.status(201).json(saved);
  } catch (err) {
    console.error("Error creating ticket:", err); // Important!
    res.status(500).json({ error: "Server error creating ticket" });
  }
});
*/


export default router;
