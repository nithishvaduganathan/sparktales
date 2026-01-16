import { useState } from "react";
import Sidebar from "../components/SideBar";
import Header from "../components/Header";

import { Bot } from "lucide-react";

function ChatPage() {
  // 1️⃣ stores all chat messages
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi 👋 How can I help you?" }
  ]);

  // 2️⃣ stores what user types
  const [input, setInput] = useState("");

  // 3️⃣ runs when user clicks Send
  function handleSend() {
    if (!input.trim()) return;

    // add user message
    const newMessages = [
      ...messages,
      { from: "user", text: input }
    ];

    setMessages(newMessages);
    setInput("");

    // fake bot reply (later replace with real AI)
    setTimeout(() => {
      setMessages(m => [
        ...m,
        { from: "bot", text: "I received: " + input }
      ]);
    }, 600);
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <div className="main-content">
        <Header />

        <div className="chat-page">
          {/* HEADER */}
          <div className="chat-header">
            <Bot size={30}></Bot> 
          </div>

          {/* MESSAGES */}
          <div className="chat-body">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={
                  msg.from === "user"
                    ? "chat-msg user"
                    : "chat-msg bot"
                }
              >
                {msg.text}
              </div>
            ))}
          </div>

          {/* INPUT */}
          <div className="chat-footer">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatPage;
