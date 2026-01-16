import { useState } from "react";
import { Bot } from "lucide-react";

function ChatBot() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Floating Button */}
      <div className="ai-float-btn" onClick={() => setOpen(true)}>
        <Bot/>
      </div>

      {/* Side Panel */}
      {open && (
        <div className="ai-panel">
          <div className="ai-panel-header">
            <span>AI Assistant</span>
            <button onClick={() => setOpen(false)}>✖</button>
          </div>

          <div className="ai-panel-body">
            <p>Hello 👋 I’m here to help you.</p>
          </div>

          <div className="ai-panel-footer">
            <input placeholder="Ask something..." />
            <button>Send</button>
          </div>
        </div>
      )}
    </>
  );
}

export default ChatBot;

