import React, { useEffect, useState } from "react";
import axios from "axios";
import TicketCard from "./TicketCard";

const AdminSupport = () => {
  const [tickets, setTickets] = useState([]);
  const UserId = localStorage.getItem("userId"); 

  useEffect(() => {
    axios.get("http://localhost:5000/api/support")
      .then(res => setTickets(res.data))
      .catch(err => console.error("Failed to fetch tickets", err));
  }, []);

  const handleRespond = async (ticketId, responseText) => {
  try {
    const res = await axios.patch(`http://localhost:5000/api/support/${ticketId}`, {
      response: responseText,
      status: "closed",
    });
    setTickets(prev =>
      prev.map(ticket => ticket._id === ticketId ? res.data : ticket)
    );
  } catch (err) {
    console.error("Error updating ticket:", err);
  }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Support Tickets</h1>
      {tickets.length === 0 ? (
        <p>No tickets yet.</p>
      ) : (
        <div className="space-y-4">
          {tickets.map(ticket => (
            <TicketCard key={ticket._id} ticket={ticket} onRespond={handleRespond} />
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminSupport;
