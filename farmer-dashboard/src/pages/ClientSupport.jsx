import React, { useEffect, useState } from "react";
import axios from "axios";

const ClientSupport = () => {
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [tickets, setTickets] = useState([]);
  const userId = localStorage.getItem("userId");

  // Submit a new ticket
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const res = await axios.post("http://localhost:5000/api/support", {
        owner: userId, // ✅ Send valid ObjectId
        subject,
        message,
      });

      console.log("Ticket submitted:", res.data);
      alert("Support ticket submitted successfully!");
      
      // Optionally, reload tickets after submitting
      setSubject("");
      setMessage("");
      setTickets(prev => [res.data, ...prev]);

    } catch (err) {
      console.error("Error submitting ticket", err);
      alert("Failed to submit ticket.");
    }
  };

  // Fetch user's tickets
  useEffect(() => {
    axios
      .get("http://localhost:5000/api/support")
      .then((res) => {
        const userTickets = res.data.filter(ticket => ticket.owner?._id === userId);
        setTickets(userTickets);
      })
      .catch((err) => console.error("Failed to load tickets", err));
  }, [userId]);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Need Help? Submit a Ticket</h2>
      <form onSubmit={handleSubmit} className="space-y-4 mb-8">
        <input
          type="text"
          className="w-full p-2 border rounded"
          placeholder="Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
        />
        <textarea
          className="w-full p-2 border rounded"
          placeholder="Describe your issue..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          required
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Submit
        </button>
      </form>

      <h3 className="text-xl font-semibold mb-2">My Support Tickets</h3>
      {tickets.length === 0 ? (
        <p className="text-gray-500">No support tickets yet.</p>
      ) : (
        <div className="space-y-4">
          {tickets.map((ticket) => (
            <div key={ticket._id} className="border p-4 rounded shadow bg-white">
              <h4 className="font-semibold">{ticket.subject}</h4>
              <p className="text-gray-700">{ticket.message}</p>
              <p className="text-sm text-gray-400">Status: {ticket.status}</p>
              {ticket.response && (
                <div className="mt-2 p-2 bg-green-50 border-l-4 border-green-400 text-green-700">
                  <p><strong>Admin Response:</strong> {ticket.response}</p>
                  <p className="text-xs text-gray-400">
                    Responded at: {new Date(ticket.respondedAt).toLocaleString()}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ClientSupport;
