function Chatbot({ onClose }) {
  return (
    <div className="chatbot-overlay">
      <div className="chatbot-box">
        <div className="chatbot-header">
          <h3>AI Assistant</h3>
          <button onClick={onClose}>✖</button>
        </div>

        <div className="chatbot-body">
          <p>Hello 👋 I’m your AI assistant.</p>
          <p>Ask me anything about your courses.</p>
        </div>

        <div className="chatbot-footer">
          <input type="text" placeholder="Type your message..." />
          <button>Send</button>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
