import { useState, useEffect } from 'react';
import './Dashboard.css';

import { Joyride } from "react-joyride";

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const PRIORITY_ORDER = { High: 0, Medium: 1, Low: 2 };
const TODAY_PAGE_SIZE = 5;

export default function Dashboard({ tasks, userId, activeTour, setActiveTour }) {
  const today = new Date();
  
  // Helper to fix timezone issues when getting date strings
  const formatLocalDate = (date) => {
    return date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
  };

  const todayStr = formatLocalDate(today);

  const [documents, setDocuments] = useState([]);
  const [journals, setJournals] = useState([]);
  const [AIJournals, setAIJournals] = useState([]);
  const [results, setResults] = useState([]);
  const [timetableEntries, setTimetableEntries] = useState([]);
  const [scheduledEntries, setScheduledEntries] = useState([]);
  const [todayPage, setTodayPage] = useState(1);

  const [runTour, setRunTour] = useState(false);

  useEffect(() => {
    if (activeTour === "dashboard") {
      setRunTour(false);
      setTimeout(() => setRunTour(true), 50);

      setActiveTour(null);
    }
  }, [activeTour]);

  useEffect(() => {
    if (userId) {
      fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/documents?user_id=${userId}`).then(r => r.json()).then(setDocuments).catch(e => console.error(e));
      fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/journals?user_id=${userId}`).then(r => r.json()).then(setJournals).catch(e => console.error(e));
      fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai_journals?user_id=${userId}`).then(r => r.json()).then(setAIJournals).catch(e => console.error(e));
      fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/quiz_results?user_id=${userId}`).then(r => r.json()).then(setResults).catch(e => console.error(e));
      // FIX: Added the missing fetches for the timetable overview
      fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/timetable?user_id=${userId}`).then(r => r.json()).then(setTimetableEntries).catch(e => console.error(e));
      fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/schedule?user_id=${userId}`).then(r => r.json()).then(setScheduledEntries).catch(e => console.error(e));
    }
  }, [userId]);

  // Today panel
  const todayItems = tasks.filter(t => t.due_date === todayStr);
  const maxTodayPages = Math.max(1, Math.ceil(todayItems.length / TODAY_PAGE_SIZE));
  const pagedTodayItems = todayItems.slice((todayPage - 1) * TODAY_PAGE_SIZE, todayPage * TODAY_PAGE_SIZE);

  // Tasks overview — top 5, sort by due_date asc then priority
  const topTasks = [...tasks]
    .sort((a, b) => {
      if (a.due_date !== b.due_date) return a.due_date < b.due_date ? -1 : 1;
      return (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3);
    })
    .slice(0, 5);

  // Timetable overview — 7 days starting today
  const timetableDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    return d;
  });

  const recentDocs = documents.slice(0, 5);
  const recentJournals = journals.slice(0, 5);

  const handleTodayPageInput = (e) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val)) setTodayPage(Math.min(maxTodayPages, Math.max(1, val)));
  };

  // Quick Stats
  const numTasks = tasks.length;

  const nextWeek = new Date();
  nextWeek.setDate(today.getDate() + 7);
  const numTasksDueNextWeek = tasks.filter(task => {
    const due_date = new Date(task.due_date);
    return due_date >= today && due_date <= nextWeek;
  }).length;

  const numDocuments = documents.length;

  const averageScore = results.length > 0 ? (results.reduce((sum, result) => sum + (result.score / result.total_questions), 0) / results.length * 100).toFixed(2) : 0;
  const averageMood = AIJournals.length > 0 ? (AIJournals.reduce((sum, journal) => sum + journal.sentiment_score, 0) / AIJournals.length).toFixed(2) : 0;

  const steps = [
    {
      target: "body",
      placement: "center",
      content: "Welcome! This dashboard gives you a quick overview of everything in your workspace."
    },
    {
      target: "#today-panel",
      content: "Your Today Panel shows tasks due today so you can focus on what matters right now."
    },
    {
      target: "#quick-stats",
      content: "Quick Stats give you a snapshot of your productivity and progress."
    },
    {
      target: "#tasks-overview",
      content: "Here are your most important upcoming tasks, sorted by urgency."
    },
    {
      target: "#timetable-overview",
      content: "Your timetable shows lectures and scheduled work across the next 7 days."
    },
    {
      target: "#academic-overview",
      content: "This section shows your most recent academic documents."
    },
    {
      target: "#journaling-overview",
      content: "Your recent journal entries appear here for reflection and tracking."
    }
  ];

  return (
    <>
    {typeof window !== "undefined" && (
      <Joyride
        steps={steps}
        run={runTour}
        continuous
        showSkipButton
        showProgress
        disableBeacon
        callback={(data) => {
          if (data.status === "finished" || data.status === "skipped") {
            setRunTour(false);
            setActiveTour(null);
          }
        }}
      />
    )}

    <div className="page">
      <div id="dashboard-grid">

        {/* Today Panel */}
        <div className="section-container" id="today-panel">
          <h2 className="section-header">Today Panel</h2>
          <div id="today-list">
            {pagedTodayItems.length === 0 ? (
              <p className="empty-msg">No events or tasks due today.</p>
            ) : (
              pagedTodayItems.map(task => (
                <div className="today-item" key={task.id}>
                  <span className="today-item-name">{task.name}</span>
                  <span className="task-meta">{task.priority}</span>
                  <span className="task-meta">{task.status}</span>
                </div>
              ))
            )}
          </div>
          <div className="pagination">
            <button onClick={() => setTodayPage(p => Math.max(1, p - 1))}>&lt;</button>
            <input type="number" value={todayPage} onChange={handleTodayPageInput} />
            <span>/ {maxTodayPages}</span>
            <button onClick={() => setTodayPage(p => Math.min(maxTodayPages, p + 1))}>&gt;</button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="section-container" id="quick-stats">
          <h2 className="section-header">Quick Stats</h2>
          <p>Number of tasks = {numTasks}</p>
          <p>Number of tasks due next week = {numTasksDueNextWeek}</p>
          <p>Number of documents = {numDocuments}</p>
          <p>Average quiz score (all attempts) = {averageScore}%</p>
          <p>Average mood score (all time) = {averageMood}</p>
        </div>

        {/* Tasks Overview */}
        <div className="section-container" id="tasks-overview">
          <h2 className="section-header">Tasks Overview</h2>
          <div id="tasks-overview-list">
            {topTasks.map(task => (
              <div className="task-row" key={task.id}>
                <span className="task-name">{task.name}</span>
                <span className="task-meta">{task.due_date}</span>
                <span className="task-meta">{task.priority}</span>
                <span className="task-meta">{task.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Timetable Overview */}
        <div className="section-container" id="timetable-overview">
          <h2 className="section-header">Timetable Overview</h2>
          <div id="timetable-overview-grid">
            <div id="timetable-overview-header">
              {timetableDays.map((d, i) => (
                <div key={i} className="cal-day-header">
                  {DAY_NAMES[d.getDay()]}<br />{d.getDate()}
                </div>
              ))}
            </div>
            <div id="timetable-overview-body">
              {timetableDays.map((d, i) => {
                const dateStr = formatLocalDate(d);
                const dayLectures = timetableEntries.filter(e => e.date === dateStr);
                const dayScheduled = scheduledEntries.filter(e => e.date === dateStr);

                return (
                  <div key={i} className="timetable-overview-cell" style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '4px', overflowY: 'auto', minHeight: 0 }}>
                    {dayLectures.map(entry => {
                      const type = (entry.type || "lecture").toLowerCase();
                      return (
                        <div key={entry.id} className={`entry ${type}`} style={{ fontSize: '0.7rem' }}>
                          {entry.start_time.slice(0, 5)} - {entry.title.split('/')[0]}
                        </div>
                      );
                    })}
                    {dayScheduled.map(entry => (
                      <div key={entry.id} className="entry-preview-title" style={{ fontSize: '0.7rem', backgroundColor: '#a855f7', color: 'white', padding: '2px 4px', borderRadius: '4px' }}>
                        {entry.start_time.slice(0, 5)} - {entry.name}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Academic Overview */}
        <div className="section-container" id="academic-overview">
          <h2 className="section-header">Academic Overview</h2>
          <div id="academic-overview-list">
            {recentDocs.map(doc => (
              <div className="overview-row" key={doc.id}>
                <span className="overview-name">{doc.file_name}</span>
                <span className="task-meta">{doc.module}</span>
                <span className="task-meta">{doc.date_uploaded}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Journaling Overview */}
        <div className="section-container" id="journaling-overview">
          <h2 className="section-header">Journaling Overview</h2>
          <div id="journaling-overview-list">
            {recentJournals.map(j => (
              <div className="overview-row" key={j.id}>
                <span className="task-meta">{j.date}</span>
                <span className="overview-name">{j.entry.length > 60 ? j.entry.slice(0, 57) + '...' : j.entry}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
    </>
  );
}