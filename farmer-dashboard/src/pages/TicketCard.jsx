import React, { useState } from "react";

const TicketCard = ({ ticket, onRespond }) => {
  const [responseText, setResponseText] = useState("");

  return (
    <div className="border rounded-xl p-4 shadow bg-white">
      <p className="text-sm text-gray-500">From: {ticket.owner?.username || ticket.owner}</p>
      <h3 className="text-lg font-semibold">{ticket.subject}</h3>
      <p className="mb-2">{ticket.message}</p>

      {ticket.status === "open" ? (
        <div className="mt-3">
          <textarea
            className="w-full p-2 border rounded"
            placeholder="Write a response..."
            value={responseText}
            onChange={e => setResponseText(e.target.value)}
          />
          <button
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={() => onRespond(ticket._id, responseText)}
          >
            Send Response
          </button>
        </div>
      ) : (
        <div className="mt-2 text-green-700">
          <p><strong>Response from:</strong> {"Support Team"}</p>
          <p><strong>Response:</strong> {ticket.response}</p>
          <p className="text-sm text-gray-400">Closed on: {new Date(ticket.respondedAt).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
};

export default TicketCard;
