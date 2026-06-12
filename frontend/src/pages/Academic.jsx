import { useState, useEffect } from 'react';
import { Line, LineChart, Bar, BarChart, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import './Academic.css';

import { Joyride } from "react-joyride";

const ITEMS_PER_PAGE = 10;

export default function Academic({ userId, activeTour, setActiveTour }) {
  const [documents, setDocuments] = useState([]);
  const [filteredDocs, setFilteredDocs] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [activeTab, setActiveTab] = useState('view');
  const [showDocModal, setShowDocModal] = useState(false);
  const [moduleFilter, setModuleFilter] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadModule, setUploadModule] = useState('');
  const [uploadTags, setUploadTags] = useState('');
  const [uploadDate, setUploadDate] = useState(new Date().toISOString().split('T')[0]);
  const [uploading, setUploading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [flashcards, setFlashcards] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentCard, setCurrentCard] = useState(0);
  const [showCurrentCardAnswer, setShowCurrentCardAnswer] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState([]);
  const [quizScore, setQuizScore] = useState(null);
  const [quizWrongAnswers, setQuizWrongAnswers] = useState([]);
  const [moduleScoresHistory, setModuleScoresHistory] = useState({});
  const [moduleScoresAverages, setModuleScoresAverages] = useState([]);
  const [needSupport, setNeedSupport] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const [runTour, setRunTour] = useState(false);

  useEffect(() => {
    if (activeTour === "academic") {
      setRunTour(false);
      setTimeout(() => setRunTour(true), 50);

      setActiveTour(null);
    }
  }, [activeTour]);

  useEffect(() => {
    setCurrentCard(0);
    setShowCurrentCardAnswer(false);
  }, [flashcards]);

  const askQuestion = async () => {
    if (! question.trim()) return;

    const response = await fetch("http://localhost:8000/ai/ask_question", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ summary: summary, question: question })
    });

    const data = await response.json();
    setAnswer(data.answer);
  }

  async function getAcademicTrends() {
    if (!userId) return;
    try {
      const response = await fetch(`http://localhost:8000/ai/academic_trends?user_id=${userId}`, {method: 'GET'});
      const data = await response.json();
      setModuleScoresHistory(data.module_scores_history);
      setModuleScoresAverages(data.module_scores_averages);
      setNeedSupport(data.need_support);
    } catch (err) {
      console.error(err.message);
    }
  }

  useEffect(() => {
    getAcademicTrends();
  }, [userId]);

  useEffect(() => {
    if (userId) {
      fetch(`http://localhost:8000/documents?user_id=${userId}`, { method: 'GET' })
        .then((response) => response.json())
        .then((data) => setDocuments(data))
        .catch(err => console.error(err));
    }
  }, [userId]);

  useEffect(() => {
    let result = [...documents];
    if (moduleFilter) result = result.filter(d => d.module === moduleFilter);
    if (tagFilter) result = result.filter(d => d.tags && d.tags.split(',').map(t => t.trim()).includes(tagFilter));
    if (searchQuery) result = result.filter(d => d.file_name.toLowerCase().includes(searchQuery.toLowerCase()));
    setFilteredDocs(result);
    setCurrentPage(1);
  }, [documents, moduleFilter, tagFilter, searchQuery]);

  useEffect(() => {
    if (quiz) {
      setQuizAnswers(Array(quiz.length).fill(null));
      setQuizScore(null);
      setQuizWrongAnswers([]);
    }
  }, [quiz]);

  useEffect(() => {
    if (! selectedDoc) return; 

    setQuestion("")
    setAnswer("")

    const getAIContent = async () => {
      try {
        const response = await fetch('http://localhost:8000/ai/' + selectedDoc.file_name, { method: 'GET' });
        const content = await response.json();

        setSummary(content.summary);
        setFlashcards(content.flashcards);
        setQuiz(content.quiz);
      } catch (err) {
        console.error(err.message);
      }
    };

    getAIContent();

  }, [selectedDoc]);

  const maxPages = Math.max(1, Math.ceil(filteredDocs.length / ITEMS_PER_PAGE));
  const pagedDocs = filteredDocs.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const moduleOptions = [...new Set(documents.map(d => d.module).filter(Boolean))];
  const tagOptions = [...new Set(
    documents.flatMap(d => d.tags ? d.tags.split(',').map(t => t.trim()).filter(Boolean) : [])
  )];

  const nextCard = () => {
    setShowCurrentCardAnswer(false);
    setCurrentCard((prev) => (prev + 1) % flashcards.length);
  };

  const prevCard = () => {
    setShowCurrentCardAnswer(false);
    setCurrentCard((prev) => prev === 0 ? flashcards.length - 1 : prev - 1); 
  };

  const openDocModal = (doc, tab) => {
    setSelectedDoc(doc);
    setActiveTab(tab);
    setShowDocModal(true);
  };

  const closeModal = () => {
    setShowDocModal(false);
    setSelectedDoc(null);
  };

  const handlePageInput = (e) => {
    const val = parseInt(e.target.value);
    if (!isNaN(val)) setCurrentPage(Math.min(maxPages, Math.max(1, val)));
  };

  const handleOverlayClick = (e) => {
    if (e.target.className === 'modal-overlay') closeModal();
  };

  const closeUploadModal = () => {
    setShowUploadModal(false);
    setUploadFile(null);
    setUploadModule('');
    setUploadTags('');
    setUploadDate(new Date().toISOString().split('T')[0]);
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('module', uploadModule);
      formData.append('tags', uploadTags);
      formData.append('date_uploaded', uploadDate);
      formData.append('user_id', userId); 

      const response = await fetch('http://localhost:8000/documents/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error(`Upload failed: ${response.status}`);

      const newDoc = await response.json();
      setDocuments(prev => [newDoc, ...prev]);
      closeUploadModal();
    } catch (err) {
      alert(err.message);
    } finally {
      setUploading(false);
    }
  };

  const generateContent = async (type) => {
    try {
      setLoading(true);

      const response = await fetch("http://localhost:8000/ai", {
        method: "POST",
        headers: { "Content-Type" : "application/json" },
        body: JSON.stringify({ file_name: selectedDoc.file_name, type: type }),
      });

      const newContent = await response.json();

      if (type === "summary") {setSummary(newContent.summary);}
      if (type === "flashcards") {setFlashcards(newContent.flashcards);}
      if (type === "quiz") {setQuiz(newContent.quiz);}
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateQuizAnswers = (updatedQuestionIndex, updatedAnswer) => {
    const updatedQuizAnswers = [...quizAnswers];
    updatedQuizAnswers[updatedQuestionIndex] = updatedAnswer;
    setQuizAnswers(updatedQuizAnswers);
  };

  const submitQuiz = async () => {
    let score = 0;
    const wrongAnswers = [];
    quiz.forEach((question, index) => {
      if (quizAnswers[index] === question.answer) {
        score ++;
      }
      else {
        wrongAnswers.push({questionNumber: index + 1, actualAnswer: question.answer});
      }
    });
    setQuizScore(score);
    setQuizWrongAnswers(wrongAnswers);

    try {
      await fetch("http://localhost:8000/ai/quiz_result", {
        method: "POST",
        headers: { "Content-Type" : "application/json" },
        body: JSON.stringify({ file_name: selectedDoc.file_name, score: score, total_questions: quiz.length, user_id: userId })
      });
    } catch (err) {
      alert(err.message);
    }

    getAcademicTrends();
  };

  const steps = [
    {
      target: "#academic-layout",
      placement: "center",
      content: "Welcome! This is your Academic page where you manage documents and track your progress."
    },
    {
      target: "#upload-btn",
      content: "Upload your academic documents here."
    },
    {
      target: "#module-filter",
      content: "Filter your documents by module."
    },
    {
      target: "#tag-filter",
      content: "Filter documents using tags."
    },
    {
      target: "#search-bar",
      content: "Quickly search for documents by name."
    },
    {
      target: "#documents-section",
      placement: "right",
      content: "This is where all your academic documents are displayed."
    },
    {
      target: "#academic-trends-section",
      placement: "left",
      content: "This section shows your academic trends and performance over time."
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
      <div id="academic-layout">

        <div className="section-container">
        <div id="control-bar">
          <button id="upload-btn" className="btn btn-primary" onClick={() => setShowUploadModal(true)}>Upload</button>
          <select id="module-filter" value={moduleFilter} onChange={(e) => setModuleFilter(e.target.value)}>
            <option value="">Filter by module</option>
            {moduleOptions.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
          <select id="tag-filter" value={tagFilter} onChange={(e) => setTagFilter(e.target.value)}>
            <option value="">Filter by tags</option>
            {tagOptions.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <input
            id="search-bar"
            type="text"
            placeholder="Search documents"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        </div>

        <div id="academic-content">
          <div className="section-container" id="documents-section">
            <h2 className="section-header">Documents List</h2>
            <div id="documents-list">
              {pagedDocs.map(doc => (
                <div className="document-bar" key={doc.id}>
                  <div className="document-info">
                    <span className="doc-title">{doc.file_name}</span>
                    <span className="doc-meta">{doc.module}</span>
                    <span className="doc-meta">{doc.date_uploaded}</span>
                  </div>
                  <div className="document-actions">
                    <button onClick={() => openDocModal(doc, 'view')}>View</button>
                    <button onClick={() => openDocModal(doc, 'summary')}>Summary</button>
                    <button onClick={() => openDocModal(doc, 'flashcards')}>Flashcards</button>
                    <button onClick={() => openDocModal(doc, 'quiz')}>Quiz</button>
                  </div>
                </div>
              ))}
            </div>
            <div className="pagination">
              <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))}>&lt;</button>
              <input type="number" value={currentPage} onChange={handlePageInput} />
              <span>/ {maxPages}</span>
              <button onClick={() => setCurrentPage(p => Math.min(maxPages, p + 1))}>&gt;</button>
            </div>
          </div>

          <div className="section-container" id="academic-trends-section">
            <h2 className="section-header">Academic Trends</h2>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={moduleScoresAverages} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                  <Bar dataKey="average_percentage_score" name="Average 1st Attempt Quiz Score" fill="grey"/>
                  <XAxis dataKey="module" stroke="black" tick={{ fontSize: 10, fill: "black" }} tickMargin={7.5} interval={0} padding={{ left: 5, right: 5 }}/>
                  <YAxis stroke="black" tick={{ fill: "black" }} domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]}/>
                  <Tooltip/>
                </BarChart>
              </ResponsiveContainer>

              {Object.entries(moduleScoresHistory).map( ([module, history]) => (
                <div key={module} className="module-trend-chart">
                  <p>{module}</p>
                    <ResponsiveContainer width="100%" height={160}>
                      <LineChart data={history} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                        <Line type="monotone" dataKey="percentage_score" name="1st Attempt Quiz Score" stroke="black" strokeWidth={2}/>
                        <XAxis dataKey="created_at" name="Time" stroke="black" tick={{ fill: "black", fontSize: 12 }} tickFormatter={(created_at) => created_at.split("T")[0]} tickMargin={7.5} interval={0} padding={{ left: 20, right: 32.5 }}/>
                        <YAxis stroke="black" tick={{ fill: "black" }} domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]}/>
                        <Tooltip labelFormatter={(timestamp) => timestamp.split("T")[0]}/>
                      </LineChart>
                  </ResponsiveContainer>
                </div>
              ))}

              {moduleScoresAverages.length == 0 && (
                <div>
                  <p>Start attempting quizzes to get insights!</p>
                </div>
              )}

              {/* UPGRADED ACADEMIC SUPPORT ALERT CARD */}
              {needSupport && (
                <div className="academic-support-card" style={{ marginTop: '20px', padding: '20px', backgroundColor: '#fff7ed', borderRadius: '8px', border: '1px solid #fed7aa' }}>
                  <h3 style={{ margin: '0 0 10px 0', color: '#c2410c', display: 'flex', alignItems: 'center', gap: '8px' }}>
                     <span>📚</span> Academic Support Recommended
                  </h3>
                  <p style={{ margin: '0 0 15px 0', fontSize: '0.9rem', color: '#9a3412', lineHeight: '1.4' }}>
                    Based on your recent quiz scores, it looks like you might be finding some modules challenging. QMUL has excellent resources, including drop-in sessions and academic advisors ready to help you succeed.
                  </p>
                  <a 
                    href="https://www.qmul.ac.uk/student-advice-and-signposting-hub/academic-support/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ display: 'inline-block', backgroundColor: '#ea580c', color: 'white', textDecoration: 'none', padding: '8px 16px', borderRadius: '4px', fontSize: '0.9rem', fontWeight: 'bold' }}
                  >
                    View QMUL Academic Support
                  </a>
                </div>
              )}
          </div>
        </div>
      </div>

      {showUploadModal && (
        <div className="modal-overlay" onClick={(e) => { if (e.target.className === 'modal-overlay') closeUploadModal(); }}>
          <div className="modal">
            <button className="modal-close" onClick={closeUploadModal}>X</button>
            <h2 className="section-header">Upload Document</h2>
            <div id="upload-form">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(e) => setUploadFile(e.target.files[0])}
              />
              <input
                type="text"
                placeholder="Module"
                value={uploadModule}
                onChange={(e) => setUploadModule(e.target.value)}
              />
              <input
                type="text"
                placeholder="Tags (comma-separated)"
                value={uploadTags}
                onChange={(e) => setUploadTags(e.target.value)}
              />
              <input
                type="date"
                value={uploadDate}
                onChange={(e) => setUploadDate(e.target.value)}
              />
              <div id="upload-form-buttons">
                <button className="btn" onClick={closeUploadModal}>Cancel</button>
                <button className="btn" onClick={handleUpload} disabled={!uploadFile || uploading}>
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showDocModal && selectedDoc && (
        <div className="modal-overlay" onClick={handleOverlayClick}>
          <div className="modal" id="doc-modal">
            <button className="modal-close" onClick={closeModal}>X</button>
            <h2 className="section-header">{selectedDoc.file_name}</h2>
            <div className="modal-tabs">
              {['view', 'summary', 'flashcards', 'quiz'].map(tab => (
                <button
                  key={tab}
                  className={`modal-tab${activeTab === tab ? ' active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
            <div id="doc-modal-content">
              {activeTab === 'view' &&
              <a href={selectedDoc.file_location} target="_blank" rel="noopener noreferrer">View Document</a>
              }
              {activeTab === 'summary' &&
              <div>
                <button className="btn btn-primary" disabled={loading} onClick={() => generateContent("summary")}>Generate Summary</button>
                {loading && <p>Thinking...</p>}
                <p>{summary}</p>
                {summary && (
                  <div className="ask-question-section">
                    <h2>Ask AI!</h2>
                    <textarea
                      placeholder="Ask AI a question about the content"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                    />
                    <button onClick={askQuestion}>Ask</button>
                    {answer && (<p className="ask-question-section-answer">{answer}</p>)}
                  </div>
                )}
              </div>
              }
              {activeTab === 'flashcards' &&
              <div>
                <button className="btn btn-primary" disabled={loading} onClick={() => generateContent("flashcards")}>Generate Flashcards</button>
                {loading && <p>Thinking...</p>}
                {flashcards && (
                  <div className="flashcard-section">
                    <h1>Card {currentCard + 1} / {flashcards.length}</h1>
                    <div className="flashcard" onClick={() => setShowCurrentCardAnswer(! showCurrentCardAnswer)}>
                      {showCurrentCardAnswer ? flashcards[currentCard]?.answer : flashcards[currentCard]?.question}
                    </div>
                    <div className="flashcard-buttons">
                      <button onClick={prevCard}>Previous</button>
                      <button onClick={nextCard}>Next</button>
                    </div>
                  </div>
                )}
              </div>
              }
              {activeTab === 'quiz' &&
              <div>
                <button className="btn btn-primary" disabled={loading} onClick={() => generateContent("quiz")}>Generate Quiz</button>
                {loading && <p>Thinking...</p>}
                {quiz && (
                  <div className="quiz-section">
                    <h1>Quiz</h1>
                    {quiz.map((question, questionIndex) => (
                      <div className="quiz-question" key={questionIndex}>
                        <p className="quiz-question-text">Question {questionIndex + 1}: {question.question}</p>
                        {question.options.map((option, optionIndex) => {
                          const letter = option.charAt(0);
                          return (
                            <div className="quiz-option" key={optionIndex}>
                              <label>
                                <input
                                  type="radio"
                                  name={"question" + questionIndex}
                                  value={letter}
                                  checked={quizAnswers[questionIndex] === letter}
                                  onChange={() => updateQuizAnswers(questionIndex, letter)}
                                />
                                {option}
                              </label>
                            </div>
                          );
                        })}
                      </div>
                    ))}
                    <button
                      className="quiz-button"
                      onClick={submitQuiz}
                      disabled={!quizAnswers.every(q => q !== null)}
                    >
                      Submit
                    </button>
                    {quizScore !== null && (
                      <div className="quiz-results">
                        <h1>Score: {quizScore} / {quiz.length}</h1>
                        {quizWrongAnswers.length > 0 && (
                          <div>
                            <p>Correct Answers:</p>
                            {quizWrongAnswers.map((item, index) => (
                              <p key={index}>Question {item.questionNumber} = {item.actualAnswer}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
              }
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
}