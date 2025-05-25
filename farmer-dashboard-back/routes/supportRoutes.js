import express from "express";
import SupportTicket from "../models/supportTicket.js";

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
/*router.patch("/:id", async (req, res) => {
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

    if (!updatedTicket) return res.status(404).json({ error: "Ticket not found." });

    res.json(updatedTicket);
  } catch (err) {
    res.status(500).json({ error: "Failed to update ticket." });
  }
});*/
// In SupportRoutes.js, update PATCH route:
router.patch("/:id", async (req, res) => {
  try {
    const { response, status, responder } = req.body; // add responder
    const updateFields = {
      ...(response && { response }),
      ...(status && { status }),
      ...(response && { respondedAt: new Date() }),
      ...(responder && { responder }), // save responder ID
    };

    const updatedTicket = await SupportTicket.findByIdAndUpdate(
      req.params.id,
      updateFields,
      { new: true }
    ).populate('owner', 'username').populate('responder', 'username'); // populate both owner and responder

    if (!updatedTicket) return res.status(404).json({ error: "Ticket not found." });

    res.json(updatedTicket);
  } catch (err) {
    res.status(500).json({ error: "Failed to update ticket." });
  }
});

// (Optional) DELETE /api/support/:id - Delete a ticket
router.delete("/:id", async (req, res) => {
  try {
    const deleted = await SupportTicket.findByIdAndDelete(req.params.id);
    if (!deleted) return res.status(404).json({ error: "Ticket not found." });
    res.json({ message: "Ticket deleted." });
  } catch (err) {
    res.status(500).json({ error: "Failed to delete ticket." });
  }
});

// POST /api/support - create new ticket
router.post("/", async (req, res) => {
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


export default router;
