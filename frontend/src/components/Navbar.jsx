import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import { useEffect, useRef, useState } from 'react';
import './Navbar.css'; 

export default function Navbar({setActiveTour}) {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState('');
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [aiSummariesEnabled, setAiSummariesEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  
  const menuRef = useRef(null);
  const location = useLocation();

  const routeToTour = {
    "/": "dashboard",
    "/academic": "academic",
    "/journaling": "journaling",
    "/tasks": "tasks",
  };

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) setUserEmail(user.email);
    });
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowAccountMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setShowAccountMenu(false);
    navigate("/");
  };

  const openSettings = () => {
    setShowAccountMenu(false);
    setShowSettingsModal(true);
  };

  const handleResetDemo = async () => {
    const confirmReset = window.confirm(
      "Reset Demo? This will wipe all your tasks, journals, and documents so you can start the demo fresh, but keep you logged in."
    );

    if (!confirmReset) return;

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const userId = user.id;
      const tables = [
        'tasks', 
        'journals', 
        'documents', 
        'timetable_entries', 
        'ai_journals', 
        'ai_documents', 
        'quiz_results', 
        'scheduled_entries'
      ];

      await Promise.all(
        tables.map(table => supabase.from(table).delete().eq('user_id', userId))
      );

      alert("Demo data has been reset successfully.");
      setShowSettingsModal(false);
      window.location.reload(); 
    } catch (error) {
      console.error(error);
      alert("There was an error resetting your data.");
    }
  };

  const handleDeleteAccount = async () => {
    const confirmDelete = window.confirm(
      "Are you absolutely sure? This will permanently delete all your tasks, journals, and documents and log you out. This cannot be undone."
    );
    
    if (!confirmDelete) return;

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const userId = user.id;
        const tables = [
          'tasks', 
          'journals', 
          'documents', 
          'timetable_entries', 
          'ai_journals', 
          'ai_documents', 
          'quiz_results', 
          'scheduled_entries'
        ];

        await Promise.all(
          tables.map(table => supabase.from(table).delete().eq('user_id', userId))
        );
        
        await supabase.auth.signOut();
        setShowSettingsModal(false);
        navigate("/");
        alert("Your account and all associated data have been deleted.");
      }
    } catch (error) {
      console.error(error);
      alert("There was an error deleting your account.");
    }
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-left">
          <span className="app-name">Student Support</span>
        </div>
        <div className="navbar-center">
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/academic">Academic</NavLink>
          <NavLink to="/journaling">Journaling</NavLink>
          <NavLink to="/tasks">Tasks</NavLink>
        </div>
        <div className="navbar-right" ref={menuRef}>
          <button className="help-button" onClick={() => setActiveTour(routeToTour[location.pathname])}>?</button>
          <button className="account-circle" onClick={() => setShowAccountMenu(v => !v)}>
            {userEmail ? userEmail[0].toUpperCase() : '?'}
          </button>
          
          {showAccountMenu && (
            <div className="account-dropdown">
              <div className="account-dropdown-header">
                Signed in as<br/><strong>{userEmail}</strong>
              </div>
              <button onClick={openSettings} className="dropdown-btn">Settings & Preferences</button>
              <button onClick={handleLogout} className="dropdown-btn logout-btn">Sign Out</button>
            </div>
          )}
        </div>
      </nav>

      {showSettingsModal && (
        <div className="modal-overlay" onClick={(e) => { if (e.target.className === 'modal-overlay') setShowSettingsModal(false); }}>
          <div className="settings-modal">
            <div className="settings-header">
              <h2>Preferences</h2>
              <button className="close-btn" onClick={() => setShowSettingsModal(false)}>X</button>
            </div>
            
            <div className="settings-section">
              <h3>Application Settings</h3>
              
              <label className="toggle-label">
                <span>Dark Mode (UI)</span>
                <input type="checkbox" checked={darkMode} onChange={(e) => setDarkMode(e.target.checked)} />
              </label>

              <label className="toggle-label">
                <span>Email Notifications for Tasks</span>
                <input type="checkbox" checked={notificationsEnabled} onChange={(e) => setNotificationsEnabled(e.target.checked)} />
              </label>

              <label className="toggle-label">
                <span>Weekly AI Insights Summary</span>
                <input type="checkbox" checked={aiSummariesEnabled} onChange={(e) => setAiSummariesEnabled(e.target.checked)} />
              </label>
            </div>

            <div className="settings-section">
              <h3>Demo Controls</h3>
              <button className="demo-reset-btn" onClick={handleResetDemo}>
                Reset Demo Data
              </button>
            </div>

            <div className="danger-zone">
              <h3>Danger Zone</h3>
              <p>Permanently delete your account and wipe all database records.</p>
              <button className="delete-account-btn" onClick={handleDeleteAccount}>
                Delete Account
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}