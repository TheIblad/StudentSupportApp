import { useState, useEffect } from 'react';
import { Line, LineChart, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import './Journaling.css';

import { Joyride } from "react-joyride";

const ENTRIES_PER_PAGE = 5;

export default function Journaling({ userId, activeTour, setActiveTour }) {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [entry, setEntry] = useState('');
  const [journals, setJournals] = useState([]);
  const [selectedJournal, setSelectedJournal] = useState(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedEntry, setEditedEntry] = useState('');
  const [entriesPage, setEntriesPage] = useState(1);
  const [moodHistory, setMoodHistory] = useState([]);
  const [recentSuggestion, setRecentSuggestion] = useState(null);
  const [needSupport, setNeedSupport] = useState(false);

  const [runTour, setRunTour] = useState(false);

  useEffect(() => {
    if (activeTour === "journaling") {
      setRunTour(false);
      setTimeout(() => setRunTour(true), 50);
      setActiveTour(null);
    }
  }, [activeTour]);

  async function loadJournals() {
    if (!userId) return;
    const response = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/journals?user_id=${userId}`, {method: "GET"});
    const data = await response.json();
    setJournals(data);
  }

  useEffect(() => {
    loadJournals();
  }, [userId]);

  async function loadJournalByDate(selectedDate) {
    if (!userId) return;
    const response = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/journals/date/${selectedDate}?user_id=${userId}`, {method: "GET"});
    const data = await response.json();
    if (data && data.entry) {
      setEntry(data.entry);
    } else {
      setEntry('');
    }
  }

  useEffect(() => {
    loadJournalByDate(date);
  }, [date, userId]);

  async function getJournalingTrends() {
    if (!userId) return;
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/journaling_trends?user_id=${userId}`, {method: "GET"});
      const data = await response.json();
      setMoodHistory(data.mood_history);
      setRecentSuggestion(data.recent_suggestion);
      setNeedSupport(data.need_support);
    } catch (err) {
      console.error(err.message);
    }
  }

  useEffect(() => {
    if (userId) {
      getJournalingTrends();
    }
  }, [userId]);

  const handleSave = async () => {
    const existingJournal = journals.find(j => j.date === date);
    const journalBody = { date: date, entry: entry, user_id: userId };

    if (existingJournal) {
      await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/journals/${existingJournal.id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(journalBody)
      });
    } else {
      await fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/journals", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(journalBody)
      });
    }

    try {
      await fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/ai/journal_analysis", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({date: date, entry: entry, user_id: userId})
      });
    } catch (err) {
      alert(err.message);
    }

    loadJournals();
    getJournalingTrends();
  };

  const handleDelete = async (id) => {
    const confirmed = window.confirm("Are you sure you want to delete this entry?");
    if (!confirmed) return;

    await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/journals/${id}`, {method: "DELETE"});
    setJournals(journals.filter(j => j.id !== id));
    setShowViewModal(false);
    getJournalingTrends();
  };

  const openJournalModal = (journal) => {
    setSelectedJournal(journal);
    setEditedEntry(journal.entry);
    setIsEditing(false);
    setShowViewModal(true);
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditedEntry(selectedJournal.entry);
    setIsEditing(false);
  };

  const handleSaveEdit = async () => {
    await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/journals/${selectedJournal.id}`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({date: selectedJournal.date, entry: editedEntry, user_id: userId})
    });

    try {
      await fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/ai/journal_analysis", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({date: selectedJournal.date, entry: editedEntry, user_id: userId})
      });
    } catch (err) {
      alert(err.message);
    }

    setJournals(journals.map(j => j.id === selectedJournal.id ? {...j, entry: editedEntry} : j));
    setSelectedJournal({...selectedJournal, entry: editedEntry});
    setIsEditing(false);
    loadJournalByDate(date);
    getJournalingTrends();
  };

  const closeModals = () => {
    setShowViewModal(false);
    setIsEditing(false);
  };

  const formatEntryPreview = (entryText) => {
    if (entryText.length > 50) {
      return entryText.substring(0, 47) + '...';
    }
    return entryText;
  };

  const maxEntriesPages = Math.max(1, Math.ceil(journals.length / ENTRIES_PER_PAGE));
  const pagedEntries = journals.slice((entriesPage - 1) * ENTRIES_PER_PAGE, entriesPage * ENTRIES_PER_PAGE);

  const handleEntriesPageInput = (e) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val)) setEntriesPage(Math.min(maxEntriesPages, Math.max(1, val)));
  };

  const steps = [
    {
      target: "#journaling-layout",
      placement: "center",
      content: "Welcome! This is your Journaling page where you write your journals and see your sentiment trend."
    },
    {
      target: "#journal-date",
      placement: "left",
      content: "Select the date you want to write your entry for.",
    },
    {
      target: "#journal-entry",
      placement: "right",
      content: "Write your thoughts here. This is your main journaling space.",
    },
    {
      target: "#save-btn",
      placement: "right",
      content: "Save your entry so it’s stored and analysed."
    },
    {
      target: "#trends-section",
      placement: "left",
      content: "This shows your sentiment trends over time based on your journal entries."
    },
    {
      target: "#recent-entries-section",
      placement: "left",
      content: "Here you can quickly access and revisit your recent entries."
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
      <div id="journaling-layout">
        <div id="left-column">
          <div className="section-container">
            <div id="journal-header-row">
              <h2 className="section-header">Journal</h2>
              <input
                type="date"
                id="journal-date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>

            <textarea
              id="journal-entry"
              placeholder="Write your journal entry..."
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
            />

            <div id="save-container">
              <button id="save-btn" className="btn" onClick={handleSave}>
                Save
              </button>
            </div>
          </div>
        </div>

        <div id="right-column">
          <div className="section-container" id="trends-section">
            <h2 className="section-header">Sentiment Trend</h2>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={moodHistory} margin={{ top: 10, right: 0, left: -35, bottom: -5 }}>
                  <Line type="monotone" dataKey="sentiment_score" stroke="black" strokeWidth={2}/>
                  <XAxis dataKey="date" stroke="black" tick={{ fontSize: 12, fill: "black" }} tickMargin={7.5} interval={0} padding={{ left: 20, right: 32.5 }}/>
                  <YAxis stroke="black" tick={{fill: "black"}} domain={[0,10]} ticks={[0, 2, 4, 6, 8, 10]}/>
                </LineChart>
              </ResponsiveContainer>

              {recentSuggestion && (
                <div className="recent-suggestion" style={{ marginTop: '15px', padding: '15px', backgroundColor: '#f8fafc', borderRadius: '8px', borderLeft: '4px solid #3b82f6' }}>
                  <h4 style={{ margin: '0 0 5px 0', color: '#1e293b', fontSize: '0.9rem' }}>AI Insight</h4>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: '#475569' }}>{recentSuggestion}</p>
                </div>
              )}

              {needSupport && (
                <div className="wellbeing-alert-card" style={{ marginTop: '20px', padding: '20px', backgroundColor: '#fff1f2', borderRadius: '8px', border: '1px solid #fecdd3' }}>
                  <h3 style={{ margin: '0 0 10px 0', color: '#e11d48', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span></span> Wellbeing Check-in
                  </h3>
                  <p style={{ margin: '0 0 15px 0', fontSize: '0.9rem', color: '#881337', lineHeight: '1.4' }}>
                    Our AI noticed your recent sentiment scores have been lower than usual. It's completely normal to have tough weeks at university. Please remember that support is always available if you need it.
                  </p>
                  <a 
                    href="https://www.nhs.uk/mental-health/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ display: 'inline-block', backgroundColor: '#e11d48', color: 'white', textDecoration: 'none', padding: '8px 16px', borderRadius: '4px', fontSize: '0.9rem', fontWeight: 'bold' }}
                  >
                    Access NHS Mental Health Resources
                  </a>
                </div>
              )}
          </div>

          <div className="section-container" id="recent-entries-section">
            <h2 className="section-header">Recent Entries</h2>

            <div id="recent-entries-list">
              {pagedEntries.map((journal) => (
                <button
                  key={journal.id}
                  className="entry-button"
                  onClick={() => openJournalModal(journal)}
                >
                  {journal.date} - {formatEntryPreview(journal.entry)}
                </button>
              ))}
            </div>

            <div className="pagination">
              <button onClick={() => setEntriesPage(p => Math.max(1, p - 1))}>&lt;</button>
              <input type="number" value={entriesPage} onChange={handleEntriesPageInput} />
              <span>/ {maxEntriesPages}</span>
              <button onClick={() => setEntriesPage(p => Math.min(maxEntriesPages, p + 1))}>&gt;</button>
            </div>
          </div>
        </div>
      </div>

      {showViewModal && selectedJournal && (
        <div className="modal-overlay" onClick={(e) => {if (e.target.className === 'modal-overlay') closeModals();}}>
          <div className="modal">
            <h2 className="section-header">{selectedJournal.date}</h2>

            <textarea
              id="modal-entry-text"
              value={isEditing ? editedEntry : selectedJournal.entry}
              onChange={(e) => setEditedEntry(e.target.value)}
              readOnly={!isEditing}
            />

            <div id="modal-buttons">
              <button className="btn" onClick={() => handleDelete(selectedJournal.id)}>
                Delete
              </button>

              {isEditing ? (
                <>
                  <button className="btn" onClick={handleCancelEdit}>
                    Cancel
                  </button>
                  <button className="btn" onClick={handleSaveEdit}>
                    Save
                  </button>
                </>
              ) : (
                <>
                  <button className="btn" onClick={closeModals}>
                    Close
                  </button>
                  <button className="btn" onClick={handleEdit}>
                    Edit
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
}