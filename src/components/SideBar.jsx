import logo from "../assets/sparktales-logo.png";
import logo1 from "../assets/photo.jpeg";

import {
  LayoutDashboard,
  BookOpen,
  BarChart3,
  Settings,
  Bot
} from "lucide-react";

import { useNavigate } from "react-router-dom";

function Sidebar({ onChatClick }) {
  const navigate = useNavigate();   // ✅ hook inside component

  return (
    <div className="sidebar">
      <div className="sidebar-top">

        <div className="logo-row">
          <div className="logo-bg">
            <img className="logo" src={logo} alt="logo" />
          </div>
          <span className="brand-name">SPARKTALES</span>
        </div>

        <div className="menu-item" onClick={() => navigate("/")}>
          <LayoutDashboard />
          <span>Dashboard</span>
        </div>

        <div className="menu-item" onClick={() => navigate("/my-courses")}>
          <BookOpen />
          <span>My Courses</span>
        </div>

        <div className="menu-item" onClick={() => navigate("/chat")}>
          <Bot />
          <span>AI Assistant</span>
        </div>

        <div className="menu-item">
          <BarChart3 />
          <span>Progress</span>
        </div>

        <div className="menu-item">
          <Settings />
          <span>Settings</span>
        </div>
      </div>

      <div className="sidebar-down">
        <img className="profile-logo" src={logo1} alt="profile" />
      </div>
    </div>
  );
}

export default Sidebar;
