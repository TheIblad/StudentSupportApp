import { useState, useEffect } from 'react';
import './Tasks.css';

import { Joyride } from "react-joyride";

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const DAY_NAMES = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
const TASKS_PER_PAGE = 8;

function getMonday(date) {
  const d = new Date(date);
  const day = d.getDay();
  d.setDate(d.getDate() - (day === 0 ? 6 : day - 1));
  d.setHours(0, 0, 0, 0);
  return d;
}

function getCalendarDays(year, month) {
  const firstDay = new Date(year, month, 1);
  const offset = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
  return Array.from({ length: 42 }, (_, i) => new Date(year, month, 1 - offset + i));
}

function getWeeksOfMonth(year, month) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const weeks = [];
  let cur = getMonday(firstDay);
  while (cur <= lastDay) {
    weeks.push(new Date(cur));
    cur = new Date(cur);
    cur.setDate(cur.getDate() + 7);
  }
  return weeks;
}

function ordinalSuffix(d) {
  if ([1, 21, 31].includes(d)) return 'st';
  if ([2, 22].includes(d)) return 'nd';
  if ([3, 23].includes(d)) return 'rd';
  return 'th';
}

function formatWeekLabel(monday) {
  const d = monday.getDate();
  return `Week of ${MONTH_NAMES[monday.getMonth()]} ${d}${ordinalSuffix(d)}`;
}

function isSameDay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function getWeekRange(monday) {
  const start = monday.toISOString().split('T')[0];
  const end = new Date(monday);
  end.setDate(end.getDate() + 6);
  return { start, end: end.toISOString().split('T')[0] };
}

// Added userId prop here
export default function Tasks({ tasks, setTasks, userId, activeTour, setActiveTour }) {
  const today = new Date();

  // View toggle
  const [calView, setCalView] = useState('month');

  // Month view navigation
  const [calYear, setCalYear] = useState(today.getFullYear());
  const [calMonth, setCalMonth] = useState(today.getMonth());

  // Week view navigation
  const [calWeekStart, setCalWeekStart] = useState(getMonday(today));

  // Date picker popup
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [pickerYear, setPickerYear] = useState(today.getFullYear());
  const [pickerMode, setPickerMode] = useState('months');
  const [pickerWeekMonth, setPickerWeekMonth] = useState(null);

  // Task filters
  const [priorityFilter, setPriorityFilter] = useState('');
  const [taskPage, setTaskPage] = useState(1);

  //Timetable modal
  const [showTimetableModal, setShowTimetableModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [entryTitle, setEntryTitle] = useState('');
  const [entryModule, setEntryModule] = useState('');
  const [entryType, setEntryType] = useState('');
  const [entryStartTime, setEntryStartTime] = useState('');
  const [entryEndTime, setEntryEndTime] = useState('');
  const [entryLocation, setEntryLocation] = useState('');
  const [entryNotes, setEntryNotes] = useState('');

  const [dayEntries, setDayEntries] = useState([]);
  const [timetableEntries, setTimetableEntries] = useState([]);

  const [scheduledEntries, setScheduledEntries] = useState([]);

  const [runTour, setRunTour] = useState(false);

  useEffect(() => {
    if (activeTour === "tasks") {
      setRunTour(false);
      setTimeout(() => setRunTour(true), 50);

      setActiveTour(null);
    }
  }, [activeTour]);

  useEffect(() => {
    const fetchSchedule = async () => {
      if (!userId) return;
      const res = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/schedule?user_id=${userId}`);
      const data = await res.json();
      setScheduledEntries(data);
    };

    fetchSchedule();
  }, [userId]);

  const refreshSchedule = async () => {
    const res = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/schedule?user_id=${userId}`);
    const data = await res.json();
    setScheduledEntries(data);
  };

  useEffect(() => {
    const fetchTimetable = async () => {
      if (!userId) return;
      const res = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/timetable?user_id=${userId}`);
      const data = await res.json();
      setTimetableEntries(data);
    };

    fetchTimetable();
  }, [userId]);

  // Add modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [addTaskName, setAddTaskName] = useState('');
  const [addTaskDescription, setAddTaskDescription] = useState('');
  const [addTaskDueDate, setAddTaskDueDate] = useState('');
  const [addTaskPriority, setAddTaskPriority] = useState('');
  const [addTaskModule, setAddTaskModule] = useState('');
  const [addTaskDuration, setAddTaskDuration] = useState('');

  // Edit modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [changeTaskID, setChangeTaskID] = useState(0);
  const [changeTaskName, setChangeTaskName] = useState('');
  const [changeTaskDescription, setChangeTaskDescription] = useState('');
  const [changeTaskDueDate, setChangeTaskDueDate] = useState('');
  const [changeTaskPriority, setChangeTaskPriority] = useState('');
  const [changeTaskStatus, setChangeTaskStatus] = useState('');
  const [changeTaskModule, setChangeTaskModule] = useState('');
  const [changeTaskDuration, setChangeTaskDuration] = useState('');

  // --- Derived values ---
  const filteredTasks = tasks.filter(t => !priorityFilter || t.priority === priorityFilter);
  const maxTaskPages = Math.max(1, Math.ceil(filteredTasks.length / TASKS_PER_PAGE));
  const pagedTasks = filteredTasks.slice((taskPage - 1) * TASKS_PER_PAGE, taskPage * TASKS_PER_PAGE);

  const todayStr = today.toISOString().split('T')[0];
  const { start: weekStart, end: weekEnd } = getWeekRange(getMonday(today));
  const tasksDueThisWeek = tasks.filter(t => t.due_date >= weekStart && t.due_date <= weekEnd).length;
  const overdueTasks = tasks.filter(t => t.due_date < todayStr && t.status !== 'Complete').length;
  const completedTotal = tasks.filter(t => t.status === 'Complete').length;

  // --- Handlers ---
  const handleTaskPageInput = (e) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val)) setTaskPage(Math.min(maxTaskPages, Math.max(1, val)));
  };

  const goToToday = () => {
    if (calView === 'month') {
      setCalMonth(today.getMonth());
      setCalYear(today.getFullYear());
    } else {
      setCalWeekStart(getMonday(today));
    }
  };

  const prevPeriod = () => {
    if (calView === 'month') {
      if (calMonth === 0) { setCalMonth(11); setCalYear(y => y - 1); }
      else setCalMonth(m => m - 1);
    } else {
      setCalWeekStart(w => { const d = new Date(w); d.setDate(d.getDate() - 7); return d; });
    }
  };

  const nextPeriod = () => {
    if (calView === 'month') {
      if (calMonth === 11) { setCalMonth(0); setCalYear(y => y + 1); }
      else setCalMonth(m => m + 1);
    } else {
      setCalWeekStart(w => { const d = new Date(w); d.setDate(d.getDate() + 7); return d; });
    }
  };

  const handlePickerMonthClick = (monthIndex) => {
    if (calView === 'month') {
      setCalMonth(monthIndex);
      setCalYear(pickerYear);
      setShowDatePicker(false);
    } else {
      setPickerWeekMonth({ year: pickerYear, month: monthIndex });
      setPickerMode('weeks');
    }
  };

  const openDatePicker = () => {
    setPickerMode('months');
    setPickerYear(calView === 'month' ? calYear : calWeekStart.getFullYear());
    setShowDatePicker(p => !p);
  };

  // Add task
  const endAdd = () => {
    // setRunAddTaskTour(false);
    setAddTaskName('');
    setAddTaskDescription('');
    setAddTaskDueDate('');
    setAddTaskPriority('');
    setAddTaskModule('');
    setAddTaskDuration('');
    setShowAddModal(false);
  };

  const addTask = async () => {
    const response = await fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        name: addTaskName, 
        description: addTaskDescription, 
        due_date: addTaskDueDate, 
        priority: addTaskPriority, 
        module: addTaskModule, 
        estimated_duration: addTaskDuration,
        user_id: userId 
      })
    });
    const addedTask = await response.json();
    setTasks([...tasks, addedTask]);
        await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/generate_schedule?user_id=${userId}`, {method: 'POST'});
        await refreshSchedule();
    endAdd();
  };

  // Edit task
  const startChange = (task) => {
    setChangeTaskID(task.id);
    setChangeTaskName(task.name);
    setChangeTaskDescription(task.description);
    setChangeTaskDueDate(task.due_date);
    setChangeTaskPriority(task.priority);
    setChangeTaskStatus(task.status);
    setChangeTaskModule(task.module);
    setChangeTaskDuration(task.estimated_duration);
    setShowEditModal(true);
  };

  const endChange = () => {
    setChangeTaskID(0);
    setChangeTaskName('');
    setChangeTaskDescription('');
    setChangeTaskDueDate('');
    setChangeTaskPriority('');
    setChangeTaskStatus('');
    setChangeTaskModule('');
    setChangeTaskDuration('');
    setShowEditModal(false);
  };

  const changeTask = async () => {
    const response = await fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/tasks/' + changeTaskID, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: changeTaskName, description: changeTaskDescription, due_date: changeTaskDueDate, priority: changeTaskPriority, status: changeTaskStatus, module: changeTaskModule, estimated_duration: changeTaskDuration })
    });
    const changedTask = await response.json();
    setTasks(tasks.map(t => t.id === changedTask.id ? changedTask : t));
        await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/generate_schedule?user_id=${userId}`, {method: 'POST'});
        await refreshSchedule();
    endChange();
  };

  const removeTask = async (id) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;
    await fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/tasks/' + id, { method: 'DELETE' });
    setTasks(tasks.filter(t => t.id !== id));
        await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/generate_schedule?user_id=${userId}`, {method: 'POST'});
        await refreshSchedule();
    endChange();
  };

  const resetTimetableForm = () => {
    setSelectedDate('');
    setEntryTitle('');
    setEntryModule('');
    setEntryType('');
    setEntryStartTime('');
    setEntryEndTime('');
    setEntryLocation('');
    setEntryNotes('');
    setDayEntries([]);
    setShowTimetableModal(false);
  };

  const addTimetableEntry = () => {
    if (!entryTitle || !entryStartTime || !entryEndTime) return;

    const newEntry = {
      title: entryTitle,
      module: entryModule,
      type: entryType,
      start_time: entryStartTime,
      end_time: entryEndTime,
      location: entryLocation,
      notes: entryNotes,
    };

    setDayEntries(prev => [...prev, newEntry]);

    // clear inputs
    setEntryTitle('');
    setEntryModule('');
    setEntryType('');
    setEntryStartTime('');
    setEntryEndTime('');
    setEntryLocation('');
    setEntryNotes('');
  };

  const saveTimetable = async () => {
    if (!selectedDate || dayEntries.length === 0) return;

    const entriesToInsert = dayEntries.map(e => ({
      ...e,
      date: selectedDate,
      user_id: userId
    }));

    await fetch((import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/timetable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entriesToInsert)
    });

    resetTimetableForm();

    // refresh timetable
    const res = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/timetable?user_id=${userId}`);
    const data = await res.json();
    setTimetableEntries(data);

    await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/generate_schedule?user_id=${userId}`, {
      method: 'POST'
    });
    await refreshSchedule();
  };

  const deleteExistingEntry = async (id) => {
    await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/timetable/${id}`, {
      method: 'DELETE'
    });

    // refresh timetable after delete
    const res = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/timetable?user_id=${userId}`);
    const data = await res.json();
    setTimetableEntries(data);

    await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/generate_schedule?user_id=${userId}`, {
      method: 'POST'
    });
    await refreshSchedule();
  };

  const deleteNewEntry = (index) => {
    const updated = [...dayEntries];
    updated.splice(index, 1);
    setDayEntries(updated);
  };

  const formatLocalDate = (date) => {
    return date.getFullYear() + '-' +
      String(date.getMonth() + 1).padStart(2, '0') + '-' +
      String(date.getDate()).padStart(2, '0');
  };

  const handleDateClick = (date) => {
    setSelectedDate(date);
    setShowTimetableModal(true);
  };

  const renderDayCell = (d, date) => {
    const lectureEntries = timetableEntries.filter(
      entry => entry.date === date
    );

    const scheduledForDay = scheduledEntries.filter(
      entry => entry.date === date
    );

    const tasksForDay = tasks.filter(task => {
      if (!task.due_date) return false;

      const taskDate = new Date(task.due_date).toISOString().slice(0, 10);
      const cellDate = new Date(date).toISOString().slice(0, 10);

      return taskDate === cellDate;
    });

    return (
      <div className="calendar-cell" style={{ cursor: "pointer" }}>
        <span className="cal-date-num">{d.getDate()}</span>

        {/* Lectures */}
        {lectureEntries.map((entry, index) => {
          const type = entry.type?.toLowerCase()

          return (
            <div key={`lec-${index}`} className={`entry ${type}`}>
              <strong>{getModuleCode(entry.title)}</strong>{" "}
              {formatTime(entry.start_time)}-{formatTime(entry.end_time)}
            </div>
          );
        })}

        {/* AI Scheduled Entries */}
        {scheduledForDay.map((entry, index) => (
          <div key={`sch-${index}`} className={`entry scheduled ${entry.category}`}>
            <strong>{entry.name}</strong>{" "}
            {formatTime(entry.start_time)}-{formatTime(entry.end_time)}
          </div>
        ))}

        {/* Tasks */}
        {tasksForDay.map((tasks, index) => (
          <div key={`task-${index}`} className="entry task">
            <strong>{tasks.name}</strong>
            <div className="task-priority">{tasks.priority}</div>
          </div>
        ))}
      </div>
    );
  };

  const existingEntriesForDay = timetableEntries.filter(
    entry => entry.date === selectedDate
  );

  const tasksForSelectedDate = tasks.filter(task => {
    if (!task.due_date) return false;
    return task.due_date === selectedDate;
  });

  const scheduledForSelectedDate = scheduledEntries.filter(entry =>
    entry.date === selectedDate
  );

  const allEntriesForPreview = [
    ...existingEntriesForDay.map(e => ({ ...e, _source: "lecture" })),
    ...dayEntries.map(e => ({ ...e, _source: "new" })),
    ...scheduledForSelectedDate.map(e => ({ ...e, _source: "scheduled" })),
    ...tasksForSelectedDate.map(t => ({ ...t, _source: "task" }))
  ];

  const handleTimetableUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", userId);

    const res = await fetch((import.meta.env.VITE_API_URL || "http://localhost:8000") + "/timetable/upload", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    // Refresh timetable after upload
    const refresh = await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/timetable?user_id=${userId}`);
    const updated = await refresh.json();
    setTimetableEntries(updated);

    await fetch(`${import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL || 'http://localhost:8000') + ''}/ai/generate_schedule?user_id=${userId}`, {
      method: 'POST'
    });
    await refreshSchedule();
  };

  const formatTime = (time) => {
    if (!time) return '';
    return time.slice(0, 5);
  };

  const getModuleCode = (title) => {
    if (!title) return '';

    const parts = title.split('/');
    return parts[0];
  };

  const steps = [
    {
      target: '#tasks-welcome',
      content: 'Welcome to your Tasks dashboard. This is where everything is organised.',
      placement: 'center',
    },
    {
      target: '#view-toggle',
      content: 'Switch between monthly and weekly views here.',
    },
    {
      target: '#priority-filter',
      content: 'Filter tasks by priority to focus on what matters most.',
    },
    {
      target: '#module-filter',
      content: 'You can also filter tasks by module.',
    },
    {
      target: '#new-task-btn',
      content: 'Create a new task here.',
    },
    {
      target: '#new-lecture-btn',
      content: 'Add lectures or timetable entries here.',
    },
    {
      target: '#upload-timetable-btn',
      content: 'Upload your timetable file here.',
    },
    {
      target: '#timetable-section',
      placement: "right",
      content: 'This is your timetable, including lectures and AI-scheduled sessions.',
    },
    {
      target: '#tasks-section',
      placement: "left",
      content: 'Here are all your tasks. Click one to edit it.',
    },
    {
      target: '#task-stats-section',
      content: 'Track your productivity and progress here.',
    },
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
      <div id="tasks-layout">

        {/* Control bar */}
        <div className="section-container" id="tasks-welcome">
          <div id="control-bar">
            <div className="toggle-group" id="view-toggle">
              <button className={`toggle-btn${calView === 'month' ? ' active' : ''}`} onClick={() => setCalView('month')}>Month</button>
              <button className={`toggle-btn${calView === 'week' ? ' active' : ''}`} onClick={() => setCalView('week')}>Week</button>
            </div>
            <select id="priority-filter" value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setTaskPage(1); }}>
              <option value="">Filter by priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>
            <select id="module-filter">
              <option value="">Filter by module</option>
            </select>
            <button id="new-task-btn" className="btn btn-primary" onClick={() => setShowAddModal(true)}>+ New Task</button>
            <button id="new-lecture-btn" className="btn btn-primary" onClick={() => setShowTimetableModal(true)}>+ New Lectures</button>
            <button id="upload-timetable-btn" className="btn btn-primary"><input type="file" accept=".html" onChange={handleTimetableUpload}/></button>
          </div>
        </div>

        {/* Main content */}
        <div id="tasks-main-content">

          {/* Timetable section */}
          <div className="section-container" id="timetable-section">
            <div id="timetable-header">
              <h2 className="section-header">Timetable</h2>
              <div id="cal-nav">
                <button id="today-btn" onClick={goToToday}>Today</button>
                <button onClick={prevPeriod}>&lt;</button>
                <button id="cal-date-btn" onClick={openDatePicker}>
                  {calView === 'month'
                    ? `${MONTH_NAMES[calMonth]} ${calYear}`
                    : formatWeekLabel(calWeekStart)}
                </button>
                <button onClick={nextPeriod}>&gt;</button>
                {showDatePicker && (
                  <div id="date-picker-popup">
                    {pickerMode === 'months' ? (
                      <>
                        <div id="picker-year-row">
                          <button onClick={() => setPickerYear(y => y - 1)}>&lt;</button>
                          <span>{pickerYear}</span>
                          <button onClick={() => setPickerYear(y => y + 1)}>&gt;</button>
                        </div>
                        <div id="picker-months-grid">
                          {MONTH_NAMES.map((m, i) => (
                            <button key={m} onClick={() => handlePickerMonthClick(i)}>{m}</button>
                          ))}
                        </div>
                      </>
                    ) : (
                      <>
                        <div id="picker-week-header">
                          <button onClick={() => setPickerMode('months')}>&lt; Back</button>
                          <span>{MONTH_NAMES[pickerWeekMonth.month]} {pickerWeekMonth.year}</span>
                        </div>
                        <div id="picker-weeks-list">
                          {getWeeksOfMonth(pickerWeekMonth.year, pickerWeekMonth.month).map(w => (
                            <button key={w.toISOString()} onClick={() => { setCalWeekStart(w); setShowDatePicker(false); }}>
                              {formatWeekLabel(w)}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div id="calendar-grid">
              <div className="calendar-header-row">
                {DAY_NAMES.map(d => <div key={d} className="cal-day-header">{d}</div>)}
              </div>
              {calView === 'month' ? (
                <div id="month-grid">
                  {getCalendarDays(calYear, calMonth).map((d, i) => {
                    const dateStr = formatLocalDate(d);
                    return (
                      <div
                        key={i}
                        className={`cal-cell${d.getMonth() !== calMonth ? ' other-month' : ''}${isSameDay(d, today) ? ' today' : ''}`}
                        onClick={() => handleDateClick(dateStr)}
                      >
                        {renderDayCell(d, dateStr)}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div id="week-grid">
                  {DAY_NAMES.map((_, i) => {
                    const d = new Date(calWeekStart);
                    d.setDate(d.getDate() + i);
                    const dateStr = formatLocalDate(d);
                    return (
                      <div
                        key={i}
                        className={`cal-cell week-cell${isSameDay(d, today) ? ' today' : ''}`}
                        onClick={() => handleDateClick(dateStr)}
                      >
                        {renderDayCell(d, dateStr)}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Tasks section */}
          <div className="section-container" id="tasks-section">
            <h2 className="section-header">Tasks</h2>
            <div id="tasks-list">
              {pagedTasks.map(task => (
                <div className="task-row" key={task.id} onClick={() => startChange(task)}>
                  <span className="task-name">{task.name}</span>
                  <span className="task-meta">{task.due_date}</span>
                  <span className="task-meta">{task.priority}</span>
                  <span className="task-meta">{task.status}</span>
                </div>
              ))}
            </div>
            <div className="pagination">
              <button onClick={() => setTaskPage(p => Math.max(1, p - 1))}>&lt;</button>
              <input type="number" value={taskPage} onChange={handleTaskPageInput}/>
              <span>/ {maxTaskPages}</span>
              <button onClick={() => setTaskPage(p => Math.min(maxTaskPages, p + 1))}>&gt;</button>
            </div>
          </div>

        </div>

        {/* Task stats */}
        <div className="section-container" id="task-stats-section">
          <h2 className="section-header">Task Stats</h2>
          <div id="stats-row">
            <div className="stat-item">
              <span className="stat-number">{tasksDueThisWeek}</span>
              <span className="stat-label">Due this week</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{overdueTasks}</span>
              <span className="stat-label">Overdue</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{completedTotal}</span>
              <span className="stat-label">Completed</span>
            </div>
          </div>
        </div>

      </div>

      {/* Add lecture modal */}
      {showTimetableModal && (
        <div className="modal-overlay" onClick={(e) => { if (e.target.className === 'modal-overlay') resetTimetableForm(); }}>
          <div className="modal timetable-modal">
            <button className="modal-close" onClick={resetTimetableForm}>X</button>
            <h2 className="section-header">Add Lecture</h2>
            <div id="timetable-form">
              <div className="tt-row">
                <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)}/>
                <input type="time" value={entryStartTime} onChange={(e) => setEntryStartTime(e.target.value)}/>
                <input type="time" value={entryEndTime} onChange={(e) => setEntryEndTime(e.target.value)}/>
              </div>
              <div className="tt-row">
                <input type="text" placeholder="Title" value={entryTitle} onChange={(e) => setEntryTitle(e.target.value)}/>
                <input type="text" placeholder="Module" value={entryModule} onChange={(e) => setEntryModule(e.target.value)}/>
                <select value={entryType} onChange={(e) => setEntryType(e.target.value)}>
                  <option value="">Type</option>
                  <option value="Lecture">Lecture</option>
                  <option value="Lab">Lab</option>
                  <option value="Tutorial">Tutorial</option>
                </select>
                <input type="text" placeholder="Location" value={entryLocation} onChange={(e) => setEntryLocation(e.target.value)}/>
              </div>
              <textarea placeholder="Notes" value={entryNotes} onChange={(e) => setEntryNotes(e.target.value)}/>
              <button className="btn" onClick={addTimetableEntry}>+ Add Entry</button>
              <div className="tt-preview">
                {allEntriesForPreview.map((e, i) => {
                  const isExistingLecture = e._source === "lecture";
                  const isNewLecture = e._source === "new";
                  const isScheduled = e._source === "scheduled";
                  const isTask = e._source === "task";

                  return (
                    <div key={i} className="entry-preview">
                      <div className="entry-preview-row">
                        <div className="entry-preview-content">
                          <div className="entry-preview-title">
                            <strong>
                              {isTask ? e.name : e.title}
                            </strong>
                            {" "}
                            {isTask ? "(Task)" : e.type ? `(${e.type})` : isScheduled ? "(Scheduled)" : ""}
                          </div>
                          {!isTask && (
                            <div className="entry-preview-time">
                              {e.start_time} - {e.end_time}
                            </div>
                          )}
                          {isTask && (
                            <>
                              <div className="entry-preview-meta">
                                Priority: {e.priority}
                              </div>
                              {e.module && (
                                <div className="entry-preview-meta">
                                  Module: {e.module}
                                </div>
                              )}
                            </>
                          )}
                          {!isTask && e.module && (
                            <div className="entry-preview-meta">
                              Module: {e.module}
                            </div>
                          )}
                          {e.location && (
                            <div className="entry-preview-meta">
                              Location: {e.location}
                            </div>
                          )}
                          {e.notes && (
                            <div className="entry-preview-notes">
                              {e.notes}
                            </div>
                          )}
                        </div>
                        {(isExistingLecture || isNewLecture) && (
                          <button className="btn" onClick={() => {
                              if (isExistingLecture) deleteExistingEntry(e.id);
                              else deleteNewEntry(e.id);
                            }}
                          >Delete</button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div id="task-form-buttons">
                <button className="btn" onClick={resetTimetableForm}>Cancel</button>
                <button className="btn" onClick={saveTimetable} disabled={!selectedDate}>Save Day</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add task modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={(e) => { if (e.target.className === 'modal-overlay') endAdd(); }}>
          <div className="modal">

            <button className="modal-close" onClick={endAdd}>X</button>
            <h2 className="section-header">Add Task</h2>
            <div id="task-form">
              <input id="task-name" type="text" placeholder="Name" value={addTaskName} onChange={(e) => setAddTaskName(e.target.value)}/>
              <textarea id="task-desc" placeholder="Description" value={addTaskDescription} onChange={(e) => setAddTaskDescription(e.target.value)}/>
              <input id="task-module" type="text" placeholder="Module" value={addTaskModule} onChange={(e) => setAddTaskModule(e.target.value)}/>
              <input id="task-duration" type="text" placeholder="Estimated Duration (a whole number in minutes)" value={addTaskDuration} onChange={(e) => setAddTaskDuration(e.target.value)}/>
              <input id="task-date" type="date" value={addTaskDueDate} onChange={(e) => setAddTaskDueDate(e.target.value)}/>
              <select id="task-priority" value={addTaskPriority} onChange={(e) => setAddTaskPriority(e.target.value)}>
                <option value="" disabled>Select Priority</option>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
              <div id="task-form-buttons">
                <button className="btn" onClick={endAdd}>Cancel</button>
                <button className="btn" onClick={addTask} disabled={!addTaskName}>Create</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit task modal */}
      {showEditModal && (
        <div className="modal-overlay" onClick={(e) => { if (e.target.className === 'modal-overlay') endChange(); }}>
          <div className="modal">
            <button className="modal-close" onClick={endChange}>X</button>
            <h2 className="section-header">Edit Task</h2>
            <div id="task-form">
              <input type="text" placeholder="Name" value={changeTaskName} onChange={(e) => setChangeTaskName(e.target.value)}/>
              <textarea placeholder="Description" value={changeTaskDescription} onChange={(e) => setChangeTaskDescription(e.target.value)}/>
              <input type="text" placeholder="Module" value={changeTaskModule} onChange={(e) => setChangeTaskModule(e.target.value)}/>
              <input type="text" placeholder="Estimated Duration (a whole number in minutes)" value={changeTaskDuration} onChange={(e) => setChangeTaskDuration(e.target.value)}/>
              <input type="date" value={changeTaskDueDate} onChange={(e) => setChangeTaskDueDate(e.target.value)}/>
              <select value={changeTaskPriority} onChange={(e) => setChangeTaskPriority(e.target.value)}>
                <option value="" disabled>Select Priority</option>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
              <select value={changeTaskStatus} onChange={(e) => setChangeTaskStatus(e.target.value)}>
                <option value="" disabled>Select Status</option>
                <option value="Incomplete - Not Started">Incomplete - Not Started</option>
                <option value="Incomplete - In Progress">Incomplete - In Progress</option>
                <option value="Complete">Complete</option>
              </select>
              <div id="task-form-buttons">
                <button className="btn" onClick={() => removeTask(changeTaskID)}>Delete</button>
                <button className="btn" onClick={endChange}>Cancel</button>
                <button className="btn" onClick={changeTask}>Update</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
}