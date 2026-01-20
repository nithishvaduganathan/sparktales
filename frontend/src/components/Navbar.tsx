import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">SparkTales LMS</Link>
      </div>
      
      <div className="navbar-menu">
        {isAuthenticated ? (
          <>
            <Link to="/dashboard" className="nav-link">Dashboard</Link>
            <Link to="/documents" className="nav-link">Documents</Link>
            <Link to="/groups" className="nav-link">Groups</Link>
            <Link to="/ai-chat" className="nav-link">AI Chat</Link>
            {user?.role === 'super_admin' && (
              <Link to="/admin" className="nav-link admin-link">Admin</Link>
            )}
            <div className="user-menu">
              <span className="user-name">{user?.full_name}</span>
              <button onClick={handleLogout} className="logout-btn">Logout</button>
            </div>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">Login</Link>
            <Link to="/register" className="nav-link">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
