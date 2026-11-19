import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from "react";
import { supabase } from './supabaseClient';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Academic from './pages/Academic';
import Journaling from './pages/Journaling';
import Tasks from './pages/Tasks';
import Login from './pages/Login';
import './App.css';

function ServerWakeBanner() {
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    let isResolved = false;

    const timer = setTimeout(() => {
      if (!isResolved) setStatus("waking");
    }, 2500);

    fetch(`${apiUrl}/`)
      .then(() => {
        isResolved = true;
        clearTimeout(timer);
        setStatus("ready");
      })
      .catch(() => {
        isResolved = true;
        clearTimeout(timer);
        setStatus("waking");
      });

    return () => clearTimeout(timer);
  }, []);

  if (status !== "waking") return null;

  return (
    <div
      style={{
        backgroundColor: "#fffbeb",
        borderBottom: "1px solid #fde68a",
        padding: "10px 16px",
        textAlign: "center",
        fontSize: "14px",
        color: "#78350f",
      }}
    >
      Brewing coffee and waking up the server (free hosting takes ~30s after a nap). Almost ready...
    </div>
  );
}

function App() {
  const [session, setSession] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [activeTour, setActiveTour] = useState(null);

  // Check for active session on load
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Fetch data only if session exists AND we have a user ID
  useEffect(() => {
    if (session?.user?.id) {
      fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/tasks?user_id=${session.user.id}`, { method: "GET" })
        .then((response) => response.json())
        .then((tasks) => setTasks(tasks))
        .catch(err => console.error("Failed to fetch tasks:", err));
    } else {
      setTasks([]); // Clear tasks if logged out
    }
  }, [session]);

  // If no session, show Login page
  if (!session) {
    return (
      <>
        <ServerWakeBanner />
        <Login />
      </>
    );
  }

  return (
    <>
      <ServerWakeBanner />
      <Navbar setActiveTour={setActiveTour} />
      <Routes>
        <Route path="/" element={<Dashboard tasks={tasks} userId={session.user.id} activeTour={activeTour} setActiveTour={setActiveTour} />} />
        {/* Pass userId down to all pages so they can save private data */}
        <Route path="/academic" element={<Academic userId={session.user.id} activeTour={activeTour} setActiveTour={setActiveTour} />} />
        <Route path="/journaling" element={<Journaling userId={session.user.id} activeTour={activeTour} setActiveTour={setActiveTour} />} />
        <Route path="/tasks" element={<Tasks tasks={tasks} setTasks={setTasks} userId={session.user.id} activeTour={activeTour} setActiveTour={setActiveTour} />} />
        {/* Redirect any unknown routes back to dashboard */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}

export default App;