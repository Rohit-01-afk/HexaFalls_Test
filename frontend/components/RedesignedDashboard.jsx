"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Form, InputGroup, Badge, Spinner, Alert, ProgressBar, Modal, Nav, Tab } from 'react-bootstrap';
import { BrandIconSvg } from './LandingPage';

const API_BASE_URL = 'http://localhost:8000';

export const RedesignedDashboard = ({
  token,
  username,
  onSignOut,
  onReturnToLanding
}) => {
  // Navigation & Active Tab State
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'pipeline' | 'vector'

  // Backend Health Status State
  const [serverHealth, setServerHealth] = useState('checking'); // 'checking' | 'online' | 'offline'

  // Document Pipeline State
  const [selectedFile, setSelectedFile] = useState(null);
  const [docId, setDocId] = useState(null);
  const [pdfFilename, setPdfFilename] = useState('');
  const [fileSizeBytes, setFileSizeBytes] = useState(0);

  // Step Statuses: 'idle' | 'loading' | 'success' | 'error'
  const [uploadStatus, setUploadStatus] = useState('idle');
  const [processStatus, setProcessStatus] = useState('idle');
  const [chunkStatus, setChunkStatus] = useState('idle');
  const [embedStatus, setEmbedStatus] = useState('idle');
  const [autoPipelineRunning, setAutoPipelineRunning] = useState(false);

  // Pipeline Output Metrics
  const [totalPages, setTotalPages] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  const [avgChunkSize, setAvgChunkSize] = useState(0);
  const [vectorCount, setVectorCount] = useState(0);
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [pipelineError, setPipelineError] = useState(null);

  // Image/Photo Attachment State
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);

  // Chat Section State
  const [inputPrompt, setInputPrompt] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'msg-welcome',
      sender: 'assistant',
      text: "Welcome to BluePrint Ai! Powered by Groq LLM (llama-3.3-70b-versatile). Upload a technical manual PDF or run the ingestion pipeline to ask grounded questions about circuit schematics, procedures, and specifications.",
      confidence: 'High',
      sources: [],
      timestamp: 'Just now',
    },
  ]);

  // Vector Search Test Bench State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTopK, setSearchTopK] = useState(5);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState(null);

  // Source Evidence Inspector Modal State
  const [inspectedSource, setInspectedSource] = useState(null);

  const filePdfInputRef = useRef(null);
  const fileImgInputRef = useRef(null);
  const chatEndRef = useRef(null);

  // Check Backend Health on Mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
          setServerHealth('online');
        } else {
          setServerHealth('offline');
        }
      } catch (err) {
        setServerHealth('offline');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Scroll Chat to Bottom on New Messages
  useEffect(() => {
    if (activeTab === 'chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isAsking, activeTab]);

  // Handle File Selection
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPdfFilename(file.name);
      setFileSizeBytes(file.size);
      // Reset pipeline progress
      setDocId(null);
      setUploadStatus('idle');
      setProcessStatus('idle');
      setChunkStatus('idle');
      setEmbedStatus('idle');
      setTotalPages(0);
      setTotalChunks(0);
      setVectorCount(0);
      setPipelineError(null);
    }
  };

  // STEP 1: Upload PDF (POST /api/v1/upload)
  const executeStep1Upload = async () => {
    if (!selectedFile) {
      setPipelineError("Please select a PDF technical manual first.");
      return null;
    }

    setUploadStatus('loading');
    setPipelineError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `Upload failed with status ${res.status}`);
      }

      const data = await res.json();
      setDocId(data.document_id);
      setPdfFilename(data.filename || selectedFile.name);
      setFileSizeBytes(data.size ?? data.file_size_bytes ?? selectedFile.size);
      setUploadStatus('success');
      return data.document_id;
    } catch (err) {
      setUploadStatus('error');
      setPipelineError(`Step 1 (Upload) Error: ${err.message}`);
      return null;
    }
  };

  // STEP 2: Process PDF (POST /api/v1/process/{doc_id})
  const executeStep2Process = async (targetDocId) => {
    const currentId = targetDocId || docId;
    if (!currentId) {
      setPipelineError("Document ID is required. Run Step 1 (Upload) first.");
      return false;
    }

    setProcessStatus('loading');
    setPipelineError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/process/${currentId}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `Processing failed with status ${res.status}`);
      }

      const data = await res.json();
      setTotalPages(data.pages ?? data.total_pages ?? 0);
      setProcessStatus('success');
      return true;
    } catch (err) {
      setProcessStatus('error');
      setPipelineError(`Step 2 (Process) Error: ${err.message}`);
      return false;
    }
  };

  // STEP 3: Chunk Document (POST /api/v1/chunk/{doc_id})
  const executeStep3Chunk = async (targetDocId) => {
    const currentId = targetDocId || docId;
    if (!currentId) {
      setPipelineError("Document ID is required. Complete Step 2 (Process) first.");
      return false;
    }

    setChunkStatus('loading');
    setPipelineError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chunk/${currentId}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `Chunking failed with status ${res.status}`);
      }

      const data = await res.json();
      setTotalChunks(data.chunks ?? data.total_chunks ?? 0);
      setAvgChunkSize(data.average_chunk_size || 0);
      setChunkStatus('success');
      return true;
    } catch (err) {
      setChunkStatus('error');
      setPipelineError(`Step 3 (Chunking) Error: ${err.message}`);
      return false;
    }
  };

  // STEP 4: Generate Embeddings (POST /api/v1/embed/{doc_id})
  const executeStep4Embed = async (targetDocId) => {
    const currentId = targetDocId || docId;
    if (!currentId) {
      setPipelineError("Document ID is required. Complete Step 3 (Chunking) first.");
      return false;
    }

    setEmbedStatus('loading');
    setPipelineError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/embed/${currentId}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `Embedding failed with status ${res.status}`);
      }

      const data = await res.json();
      setVectorCount(data.indexed_chunks ?? data.vector_count ?? 0);
      setEmbeddingModel(data.embedding_model || 'sentence-transformers');
      setEmbedStatus('success');
      return true;
    } catch (err) {
      setEmbedStatus('error');
      setPipelineError(`Step 4 (Embedding) Error: ${err.message}`);
      return false;
    }
  };

  // RUN ALL 4 PIPELINE STEPS AUTOMATICALLY
  const handleRunFullPipeline = async () => {
    if (!selectedFile) {
      setPipelineError("Please select a PDF technical manual to process.");
      return;
    }

    setAutoPipelineRunning(true);
    setPipelineError(null);

    const newDocId = await executeStep1Upload();
    if (!newDocId) {
      setAutoPipelineRunning(false);
      return;
    }

    const step2Success = await executeStep2Process(newDocId);
    if (!step2Success) {
      setAutoPipelineRunning(false);
      return;
    }

    const step3Success = await executeStep3Chunk(newDocId);
    if (!step3Success) {
      setAutoPipelineRunning(false);
      return;
    }

    await executeStep4Embed(newDocId);
    setAutoPipelineRunning(false);
  };

  // Handle Photo Attachment
  const handleImgUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedPhoto(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // ASK ENDPOINT (POST /api/v1/ask)
  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if ((!inputPrompt.trim() && !selectedPhoto) || isAsking) return;

    const userQuestion = inputPrompt.trim();
    const currentPhoto = photoPreview;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: userQuestion || 'Attached schematic photo for analysis.',
      photoUrl: currentPhoto || undefined,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt('');
    setSelectedPhoto(null);
    setPhotoPreview(null);
    setIsAsking(true);

    try {
      const payload = {
        question: userQuestion || 'Analyze attached schematic diagram',
      };
      if (docId) {
        payload.document_id = docId;
      }

      const res = await fetch(`${API_BASE_URL}/api/v1/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || errData.detail || `Query failed with status ${res.status}`);
      }

      const data = await res.json();

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: data.answer,
        confidence: data.confidence,
        sources: data.sources || [],
        metrics: data.metrics || null,
        diagnostics: data.diagnostics || null,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `Error connecting to RAG Service: ${err.message}. Ensure backend is running at http://localhost:8000 and the PDF manual has been processed.`,
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsAsking(false);
    }
  };

  // SEARCH ENDPOINT (POST /api/v1/search)
  const handleExecuteVectorSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    setSearchError(null);
    setSearchResults([]);

    try {
      const payload = {
        query: searchQuery.trim(),
        top_k: Number(searchTopK),
      };
      if (docId) {
        payload.document_id = docId;
      }

      const res = await fetch(`${API_BASE_URL}/api/v1/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || `Search failed with status ${res.status}`);
      }

      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err) {
      setSearchError(`Search Error: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  // Helper function for rendering status badges (Working = Blue, Success = Green, Error = Red)
  const renderStatusBadge = (status, label) => {
    if (status === 'loading') {
      return (
        <Badge className="bp-badge-working font-monospace py-1.5 px-3 d-inline-flex align-items-center gap-1.5 rounded-pill">
          <Spinner animation="border" size="sm" style={{ width: '0.75rem', height: '0.75rem', color: '#ffffff' }} /> Working...
        </Badge>
      );
    }
    if (status === 'success') {
      return (
        <Badge className="bp-badge-success font-monospace py-1.5 px-3 rounded-pill">
          <i className="fa-solid fa-circle-check me-1"></i> {label || 'Completed'}
        </Badge>
      );
    }
    if (status === 'error') {
      return (
        <Badge className="bp-badge-error font-monospace py-1.5 px-3 rounded-pill">
          <i className="fa-solid fa-circle-xmark me-1"></i> Error
        </Badge>
      );
    }
    return (
      <Badge bg="dark" className="border border-secondary text-secondary font-monospace py-1.5 px-3 rounded-pill">
        Pending
      </Badge>
    );
  };

  // Helper function for step action buttons
  const renderStepButton = (stepNum, onClickAction, isDisabled, status) => {
    if (status === 'loading') {
      return (
        <Button disabled className="btn-working-custom py-1.5 px-3.5 font-monospace text-xs rounded-pill d-inline-flex align-items-center gap-1.5">
          <Spinner animation="border" size="sm" style={{ width: '0.75rem', height: '0.75rem', color: '#ffffff' }} /> Working...
        </Button>
      );
    }
    return (
      <Button
        onClick={onClickAction}
        disabled={isDisabled}
        className="btn-success-custom py-1.5 px-3.5 font-monospace text-xs rounded-pill"
      >
        Run Step {stepNum}
      </Button>
    );
  };

  return (
    <div className="vh-100 vw-100 d-flex flex-column dashboard-workbench-bg">
      {/* Top Navbar */}
      <nav className="navbar navbar-expand-lg bp-nav px-4 py-2 shrink-0 border-bottom" style={{ borderColor: 'var(--border-gray)' }}>
        <Container fluid className="px-0">
          <a className="navbar-brand d-flex align-items-center gap-2 font-monospace text-light" href="#">
            <BrandIconSvg size={28} />
            <span className="brand-title-text text-light">BluePrint <span className="text-emerald">Ai</span></span>
            <span className="badge-emerald ms-2 font-monospace">Workbench Dashboard</span>
          </a>

          {/* Navigation Feature Tabs */}
          <Nav variant="pills" className="ms-4 gap-2 font-monospace text-xs" activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
            <Nav.Item>
              <Nav.Link eventKey="chat" className={`py-1.5 px-3 rounded-pill d-flex align-items-center gap-2 ${activeTab === 'chat' ? 'btn-success-custom text-white fw-bold' : 'text-light border border-secondary'}`}>
                <i className="fa-solid fa-comments text-emerald"></i> RAG Chatbot
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="pipeline" className={`py-1.5 px-3 rounded-pill d-flex align-items-center gap-2 ${activeTab === 'pipeline' ? 'btn-success-custom text-white fw-bold' : 'text-light border border-secondary'}`}>
                <i className="fa-solid fa-diagram-project text-emerald"></i> API Pipeline (1→4)
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="vector" className={`py-1.5 px-3 rounded-pill d-flex align-items-center gap-2 ${activeTab === 'vector' ? 'btn-success-custom text-white fw-bold' : 'text-light border border-secondary'}`}>
                <i className="fa-solid fa-magnifying-glass text-emerald"></i> Vector Search
              </Nav.Link>
            </Nav.Item>
          </Nav>

          <div className="d-flex align-items-center gap-3 ms-auto">
            {/* Backend Server Health Indicator */}
            <span
              className="badge px-3 py-1.5 rounded-pill font-monospace text-xs d-flex align-items-center gap-2 text-white fw-bold shadow-sm"
              style={{
                backgroundColor: serverHealth === 'online' ? '#16a34a' : '#dc2626',
                color: '#ffffff',
                border: 'none',
              }}
            >
              <span
                className="rounded-circle d-inline-block bg-white"
                style={{ width: '8px', height: '8px' }}
              ></span>
              <span>Backend: {serverHealth === 'online' ? 'Online (8000)' : 'Offline'}</span>
            </span>

            <Button onClick={onReturnToLanding} className="btn-success-custom py-1 px-3 text-xs rounded-pill">
              <i className="fa-solid fa-house me-1"></i> Home
            </Button>

            {onSignOut && (
              <Button onClick={onSignOut} className="btn-success-custom py-1 px-3 text-xs rounded-pill">
                <i className="fa-solid fa-right-from-bracket me-1"></i> Sign Out
              </Button>
            )}
          </div>
        </Container>
      </nav>

      {/* Main Workspace Body */}
      <Container fluid className="flex-grow-1 p-3 overflow-hidden">
        {/* Hidden Global PDF Input */}
        <input
          type="file"
          ref={filePdfInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          className="d-none"
        />

        {/* TAB 1: RAG CHATBOT WORKSPACE */}
        {activeTab === 'chat' && (
          <Row className="h-100 g-3">
            {/* Left Sidebar: Document Metadata & Ingestion Quick Control */}
            <Col lg={4} xl={3} className="h-100">
              <Card className="bp-card dashboard-card h-100 text-light p-3 d-flex flex-column overflow-auto">
                <div className="border-bottom pb-3 mb-3" style={{ borderColor: 'var(--border-gray)' }}>
                  <small className="text-secondary font-monospace d-block text-uppercase fw-bold mb-1">Active AI LLM Model</small>
                  <div className="d-flex align-items-center gap-2">
                    <i className="fa-solid fa-brain text-emerald fs-5"></i>
                    <div>
                      <span className="fw-bold font-monospace text-light fs-6">Groq Llama 3.3</span>
                      <small className="d-block text-secondary" style={{ fontSize: '10px' }}>llama-3.3-70b-versatile</small>
                    </div>
                  </div>
                </div>

                <div className="border-bottom pb-3 mb-3" style={{ borderColor: 'var(--border-gray)' }}>
                  <div className="d-flex align-items-center justify-content-between mb-1">
                    <small className="text-secondary font-monospace text-uppercase fw-bold">Active Manual PDF</small>
                    <Button
                      onClick={() => filePdfInputRef.current?.click()}
                      size="sm"
                      className="btn-success-custom py-0 px-2.5 text-xs font-monospace rounded-pill"
                    >
                      Choose PDF
                    </Button>
                  </div>
                  {pdfFilename ? (
                    <div className="d-flex align-items-center gap-2 text-truncate mt-1">
                      <i className="fa-solid fa-file-pdf text-emerald fs-5"></i>
                      <span className="font-monospace text-light text-truncate text-xs fw-bold" title={pdfFilename}>
                        {pdfFilename}
                      </span>
                    </div>
                  ) : (
                    <small className="text-secondary font-monospace text-xs d-block italic">No PDF uploaded yet.</small>
                  )}
                </div>

                {/* Pipeline Quick Status Card */}
                <div className="p-3 mb-3 rounded-3 border" style={{ backgroundColor: '#070c07', borderColor: 'var(--border-gray)' }}>
                  <small className="text-emerald font-monospace d-block text-uppercase fw-bold mb-2.5" style={{ fontSize: '11px', letterSpacing: '0.5px' }}>
                    <i className="fa-solid fa-server me-1.5"></i> Ingestion Status
                  </small>
                  <div className="d-flex flex-column gap-2 font-monospace text-xs">
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="text-light fw-medium">Doc ID:</span>
                      <span className="badge bg-dark border border-emerald text-emerald font-monospace px-2 py-1">{docId ? `${docId.substring(0, 8)}...` : 'None'}</span>
                    </div>
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="text-light fw-medium">Total Pages:</span>
                      <span className="badge bg-dark border border-emerald text-emerald font-monospace px-2 py-1">{totalPages > 0 ? totalPages : '0'}</span>
                    </div>
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="text-light fw-medium">Chunks:</span>
                      <span className="badge bg-dark border border-emerald text-emerald font-monospace px-2 py-1">{totalChunks > 0 ? totalChunks : '0'}</span>
                    </div>
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="text-light fw-medium">Vectors:</span>
                      <span className="badge bg-dark border border-emerald text-emerald font-monospace px-2 py-1">{vectorCount > 0 ? vectorCount : '0'}</span>
                    </div>
                  </div>
                </div>

                {/* Quick Pipeline Run Button: Blue when Working, Green when ready */}
                <Button
                  onClick={handleRunFullPipeline}
                  disabled={!selectedFile || autoPipelineRunning}
                  className={`${autoPipelineRunning ? 'btn-working-custom' : 'btn-success-custom'} w-100 py-2.5 font-monospace text-xs d-flex align-items-center justify-content-center gap-2 mb-3 rounded-pill`}
                >
                  {autoPipelineRunning ? (
                    <>
                      <Spinner animation="border" size="sm" style={{ color: '#ffffff' }} />
                      <span>Working (Steps 1→4)...</span>
                    </>
                  ) : (
                    <>
                      <i className="fa-solid fa-bolt me-1"></i>
                      <span>Auto Ingest PDF (1→4)</span>
                    </>
                  )}
                </Button>

                <Button
                  onClick={() => setActiveTab('pipeline')}
                  className="btn-success-custom w-100 py-2 font-monospace text-xs d-flex align-items-center justify-content-center gap-2 rounded-pill"
                >
                  <i className="fa-solid fa-sliders"></i>
                  <span>Manage API Pipeline</span>
                </Button>
              </Card>
            </Col>

            {/* Right Main Chat Panel */}
            <Col lg={8} xl={9} className="h-100">
              <Card className="bp-card dashboard-card h-100 text-light d-flex flex-column overflow-hidden">
                {/* Header */}
                <Card.Header className="bg-transparent border-bottom p-3 d-flex align-items-center justify-content-between" style={{ borderColor: 'var(--border-gray)' }}>
                  <div className="d-flex align-items-center gap-2 font-monospace">
                    <i className="fa-solid fa-robot text-emerald fs-5"></i>
                    <div>
                      <span className="fw-bold text-light fs-6">BluePrint Ai RAG Chatbot</span>
                      <small className="text-secondary d-block" style={{ fontSize: '11px' }}>POST /api/v1/ask Endpoint</small>
                    </div>
                  </div>

                  <div className="d-flex align-items-center gap-2">
                    <input
                      type="file"
                      ref={fileImgInputRef}
                      onChange={handleImgUpload}
                      accept="image/*"
                      className="d-none"
                    />
                    <Button
                      onClick={() => fileImgInputRef.current?.click()}
                      className="btn-success-custom py-1.5 px-3.5 font-monospace text-xs d-flex align-items-center gap-1 rounded-pill"
                    >
                      <i className="fa-solid fa-camera me-1"></i>
                      <span>Attach Photo</span>
                    </Button>
                  </div>
                </Card.Header>

                {/* Photo Attachment Bar */}
                {photoPreview && (
                  <div className="px-4 py-2 border-bottom bg-dark d-flex align-items-center justify-content-between" style={{ borderColor: 'var(--border-gray)' }}>
                    <div className="d-flex align-items-center gap-2">
                      <small className="text-emerald font-monospace text-xs fw-bold">Photo Attached:</small>
                      <img src={photoPreview} alt="Attached schematic" className="rounded object-fit-cover" style={{ height: '36px', width: '60px' }} />
                    </div>
                    <Button
                      onClick={() => { setSelectedPhoto(null); setPhotoPreview(null); }}
                      size="sm"
                      className="btn-danger py-0 px-2 text-xs font-monospace rounded-pill"
                    >
                      Remove
                    </Button>
                  </div>
                )}

                {/* Messages Body */}
                <Card.Body className="flex-grow-1 overflow-auto p-4 space-y-4">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`d-flex gap-3 mb-4 ${msg.sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
                    >
                      {msg.sender === 'assistant' && (
                        <div className="p-2 rounded bg-emerald d-flex align-items-center justify-content-center align-self-start mt-1" style={{ width: '32px', height: '32px', flexShrink: 0 }}>
                          <i className="fa-solid fa-brain text-dark"></i>
                        </div>
                      )}

                      <div
                        className={`p-3 rounded-3 shadow-sm ${
                          msg.isError
                            ? 'bp-msg-error'
                            : msg.sender === 'user'
                            ? 'chat-bubble-user'
                            : 'chat-bubble-ai'
                        }`}
                        style={{ maxWidth: '85%' }}
                      >
                        {msg.photoUrl && (
                          <div className="mb-2 rounded overflow-hidden border border-secondary">
                            <img src={msg.photoUrl} alt="Attached photo" className="w-100 object-fit-cover" style={{ maxHeight: '200px' }} />
                          </div>
                        )}

                        <div className="whitespace-pre-wrap font-sans" style={{ lineHeight: '1.6' }}>{msg.text}</div>

                        {/* Assistant Response Metadata & Sources */}
                        {msg.sender === 'assistant' && !msg.isError && (
                          <div className="mt-3 pt-2 border-top border-secondary space-y-2">
                            <div className="d-flex flex-wrap align-items-center justify-content-between gap-2">
                              {msg.confidence && (
                                <div className="d-flex align-items-center gap-1">
                                  <small className="text-secondary font-monospace" style={{ fontSize: '11px' }}>Confidence:</small>
                                  <Badge
                                    bg="dark"
                                    className={`font-monospace text-xs border ${
                                      msg.confidence === 'High' ? 'border-success text-success' :
                                      msg.confidence === 'Medium' ? 'border-warning text-warning' :
                                      msg.confidence === 'Low' ? 'border-info text-info' : 'border-secondary text-secondary'
                                    }`}
                                  >
                                    {msg.confidence}
                                  </Badge>
                                </div>
                              )}

                              {msg.metrics && (
                                <small className="text-secondary font-monospace" style={{ fontSize: '10px' }}>
                                  <i className="fa-solid fa-gauge-high me-1 text-emerald"></i>
                                  Total: {msg.metrics.total_ms || 0}ms (LLM: {msg.metrics.generation_ms || 0}ms)
                                </small>
                              )}
                            </div>

                            {/* Clickable Sources List */}
                            {msg.sources && msg.sources.length > 0 && (
                              <div>
                                <small className="text-secondary font-monospace d-block mb-1" style={{ fontSize: '11px' }}>
                                  <i className="fa-solid fa-book-bookmark text-emerald me-1"></i> Grounded Sources:
                                </small>
                                <div className="d-flex flex-wrap gap-1.5">
                                  {msg.sources.map((src, idx) => (
                                    <Button
                                      key={idx}
                                      onClick={() => setInspectedSource(src)}
                                      size="sm"
                                      className="btn-success-custom font-monospace text-xs py-0.5 px-2.5 rounded-pill d-inline-flex align-items-center gap-1"
                                    >
                                      <i className="fa-solid fa-eye text-white"></i> Page {src.page} (Score: {src.score ? src.score.toFixed(2) : 'N/A'})
                                    </Button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        <small className="d-block text-end opacity-75 mt-2 font-monospace" style={{ fontSize: '10px' }}>
                          {msg.timestamp}
                        </small>
                      </div>

                      {msg.sender === 'user' && (
                        <div className="p-2 rounded bg-dark border border-secondary text-light d-flex align-items-center justify-content-center align-self-start mt-1" style={{ width: '32px', height: '32px', flexShrink: 0 }}>
                          <i className="fa-solid fa-user"></i>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Working Indicator: Blue Background & White Text */}
                  {isAsking && (
                    <div className="d-flex align-items-center gap-3 p-3 bp-badge-working font-monospace text-xs rounded-3 shadow">
                      <Spinner animation="border" size="sm" style={{ color: '#ffffff' }} />
                      <span>Working: Generating grounded answer via Groq LLM...</span>
                    </div>
                  )}

                  <div ref={chatEndRef} />
                </Card.Body>

                {/* Prompt Quick Shortcuts */}
                <div className="px-3 py-2 bg-dark bg-opacity-75 border-top d-flex align-items-center gap-2 overflow-x-auto" style={{ borderColor: 'var(--border-gray)' }}>
                  <small className="text-secondary font-monospace text-uppercase fw-bold shrink-0" style={{ fontSize: '10px' }}>Quick Prompts:</small>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    onClick={() => setInputPrompt("What are the main technical procedures described in this manual?")}
                    className="text-light text-nowrap rounded-pill font-monospace text-xs py-0.5 px-2.5"
                  >
                    Technical procedures
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    onClick={() => setInputPrompt("What are the safety warnings and high voltage instructions?")}
                    className="text-light text-nowrap rounded-pill font-monospace text-xs py-0.5 px-2.5"
                  >
                    Safety & voltage warnings
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    onClick={() => setInputPrompt("Explain the circuit pinout and component connections")}
                    className="text-light text-nowrap rounded-pill font-monospace text-xs py-0.5 px-2.5"
                  >
                    Circuit pinouts
                  </Button>
                </div>

                {/* Input Bar */}
                <Card.Footer className="bg-transparent border-top p-3" style={{ borderColor: 'var(--border-gray)' }}>
                  <Form onSubmit={handleSendMessage}>
                    <div className="d-flex align-items-center gap-3">
                      <Form.Control
                        type="text"
                        value={inputPrompt}
                        onChange={(e) => setInputPrompt(e.target.value)}
                        placeholder="Ask any question about the technical manual, circuit diagram, or schematic..."
                        className="bg-dark text-light border-secondary font-sans py-2.5 px-4 flex-grow-1"
                        style={{ borderRadius: '50px', border: '1px solid var(--border-gray)' }}
                      />
                      <Button
                        type="submit"
                        disabled={isAsking || (!inputPrompt.trim() && !selectedPhoto)}
                        className={`${isAsking ? 'btn-working-custom' : 'btn-success-custom'} px-4 py-2.5 font-monospace text-xs shrink-0 d-flex align-items-center gap-2`}
                        style={{ borderRadius: '50px' }}
                      >
                        {isAsking ? (
                          <><Spinner animation="border" size="sm" style={{ color: '#ffffff' }} /> Working...</>
                        ) : (
                          <><i className="fa-solid fa-paper-plane"></i> Send Query</>
                        )}
                      </Button>
                    </div>
                  </Form>
                </Card.Footer>
              </Card>
            </Col>
          </Row>
        )}

        {/* TAB 2: API PIPELINE CONTROLS (1 -> 4) */}
        {activeTab === 'pipeline' && (
          <Row className="h-100 justify-content-center">
            <Col lg={10} xl={9} className="h-100">
              <Card className="bp-card dashboard-card h-100 text-light p-4 d-flex flex-column overflow-auto">
                <div className="d-flex align-items-center justify-content-between border-bottom pb-3 mb-4" style={{ borderColor: 'var(--border-gray)' }}>
                  <div>
                    <h5 className="fw-bold font-monospace text-emerald mb-1">
                      <i className="fa-solid fa-diagram-project me-2"></i> Technical Manual Ingestion Pipeline
                    </h5>
                    <small className="text-secondary d-block">Execute individual REST API endpoints or trigger the automated 4-step pipeline.</small>
                  </div>
                  <Button
                    onClick={handleRunFullPipeline}
                    disabled={!selectedFile || autoPipelineRunning}
                    className={`${autoPipelineRunning ? 'btn-working-custom' : 'btn-success-custom'} py-2 px-4 font-monospace text-xs d-flex align-items-center gap-2 rounded-pill`}
                  >
                    {autoPipelineRunning ? (
                      <>
                        <Spinner animation="border" size="sm" style={{ color: '#ffffff' }} />
                        <span>Working (Steps 1→4)...</span>
                      </>
                    ) : (
                      <>
                        <i className="fa-solid fa-play"></i>
                        <span>Run Full Pipeline</span>
                      </>
                    )}
                  </Button>
                </div>

                {/* Error Banner: Red Background with White Text */}
                {pipelineError && (
                  <Alert className="bp-alert-error py-2.5 px-3.5 text-xs font-monospace mb-4 rounded-3 d-flex align-items-center gap-2">
                    <i className="fa-solid fa-circle-exclamation text-white fs-5"></i>
                    <span>{pipelineError}</span>
                  </Alert>
                )}

                {/* File Select Banner */}
                <div className="p-3 mb-4 rounded border d-flex align-items-center justify-content-between" style={{ backgroundColor: '#050905', borderColor: 'var(--border-gray)' }}>
                  <div className="d-flex align-items-center gap-3">
                    <div className="p-3 rounded bg-emerald bg-opacity-10 border border-emerald text-emerald">
                      <i className="fa-solid fa-file-pdf fs-4"></i>
                    </div>
                    <div>
                      <small className="text-secondary font-monospace text-uppercase fw-bold d-block">Selected Document</small>
                      <span className="fw-bold text-light font-monospace fs-6">
                        {pdfFilename || 'No PDF file selected'}
                      </span>
                      {fileSizeBytes > 0 && (
                        <small className="text-secondary font-monospace ms-2">({Math.round(fileSizeBytes / 1024)} KB)</small>
                      )}
                    </div>
                  </div>
                  <Button
                    onClick={() => filePdfInputRef.current?.click()}
                    className="btn-success-custom py-2 px-4 font-monospace text-xs rounded-pill"
                  >
                    Browse PDF File
                  </Button>
                </div>

                {/* Pipeline Step Cards Grid */}
                <Row className="g-4 mb-4">
                  {/* Step 1 Card */}
                  <Col md={6}>
                    <div className="p-4 rounded-3 border h-100 d-flex flex-column justify-content-between shadow-sm" style={{ backgroundColor: '#070c07', borderColor: uploadStatus === 'success' ? '#22c55e' : 'var(--border-gray)' }}>
                      <div>
                        <div className="d-flex align-items-center justify-content-between mb-3">
                          <span className="badge-emerald font-monospace px-3 py-1 fs-6">STEP 1: UPLOAD</span>
                          {renderStatusBadge(uploadStatus, 'Uploaded')}
                        </div>
                        <h6 className="fw-bold text-light font-monospace mb-2">POST /api/v1/upload</h6>
                        <p className="text-secondary text-xs mb-3" style={{ lineHeight: '1.6' }}>
                          Uploads raw PDF manual to server storage and creates a unique Document UUID.
                        </p>
                      </div>
                      <div className="border-top pt-3 mt-3 d-flex align-items-center justify-content-between" style={{ borderColor: 'var(--border-gray)' }}>
                        <small className="font-monospace text-xs text-secondary">
                          Doc ID: <strong className="text-emerald">{docId ? `${docId.substring(0, 10)}...` : 'None'}</strong>
                        </small>
                        {renderStepButton(1, () => executeStep1Upload(), !selectedFile || uploadStatus === 'loading' || autoPipelineRunning, uploadStatus)}
                      </div>
                    </div>
                  </Col>

                  {/* Step 2 Card */}
                  <Col md={6}>
                    <div className="p-4 rounded-3 border h-100 d-flex flex-column justify-content-between shadow-sm" style={{ backgroundColor: '#070c07', borderColor: processStatus === 'success' ? '#22c55e' : 'var(--border-gray)' }}>
                      <div>
                        <div className="d-flex align-items-center justify-content-between mb-3">
                          <span className="badge-emerald font-monospace px-3 py-1 fs-6">STEP 2: PROCESS</span>
                          {renderStatusBadge(processStatus, 'Processed')}
                        </div>
                        <h6 className="fw-bold text-light font-monospace mb-2">POST /api/v1/process/{'{doc_id}'}</h6>
                        <p className="text-secondary text-xs mb-3" style={{ lineHeight: '1.6' }}>
                          Extracts text per page and renders high-res 150 DPI PNG scans for visual diagram inspection.
                        </p>
                      </div>
                      <div className="border-top pt-3 mt-3 d-flex align-items-center justify-content-between" style={{ borderColor: 'var(--border-gray)' }}>
                        <small className="font-monospace text-xs text-secondary">
                          Total Pages: <strong className="text-emerald">{totalPages > 0 ? totalPages : '0'}</strong>
                        </small>
                        {renderStepButton(2, () => executeStep2Process(), !docId || processStatus === 'loading' || autoPipelineRunning, processStatus)}
                      </div>
                    </div>
                  </Col>

                  {/* Step 3 Card */}
                  <Col md={6}>
                    <div className="p-4 rounded-3 border h-100 d-flex flex-column justify-content-between shadow-sm" style={{ backgroundColor: '#070c07', borderColor: chunkStatus === 'success' ? '#22c55e' : 'var(--border-gray)' }}>
                      <div>
                        <div className="d-flex align-items-center justify-content-between mb-3">
                          <span className="badge-emerald font-monospace px-3 py-1 fs-6">STEP 3: CHUNK</span>
                          {renderStatusBadge(chunkStatus, 'Chunked')}
                        </div>
                        <h6 className="fw-bold text-light font-monospace mb-2">POST /api/v1/chunk/{'{doc_id}'}</h6>
                        <p className="text-secondary text-xs mb-3" style={{ lineHeight: '1.6' }}>
                          Splits document text into metadata-bound chunks preserving document ID & page numbers.
                        </p>
                      </div>
                      <div className="border-top pt-3 mt-3 d-flex align-items-center justify-content-between" style={{ borderColor: 'var(--border-gray)' }}>
                        <small className="font-monospace text-xs text-secondary">
                          Total Chunks: <strong className="text-emerald">{totalChunks > 0 ? totalChunks : '0'}</strong>
                        </small>
                        {renderStepButton(3, () => executeStep3Chunk(), !docId || processStatus !== 'success' || chunkStatus === 'loading' || autoPipelineRunning, chunkStatus)}
                      </div>
                    </div>
                  </Col>

                  {/* Step 4 Card */}
                  <Col md={6}>
                    <div className="p-4 rounded-3 border h-100 d-flex flex-column justify-content-between shadow-sm" style={{ backgroundColor: '#070c07', borderColor: embedStatus === 'success' ? '#22c55e' : 'var(--border-gray)' }}>
                      <div>
                        <div className="d-flex align-items-center justify-content-between mb-3">
                          <span className="badge-emerald font-monospace px-3 py-1 fs-6">STEP 4: EMBED</span>
                          {renderStatusBadge(embedStatus, 'Embedded')}
                        </div>
                        <h6 className="fw-bold text-light font-monospace mb-2">POST /api/v1/embed/{'{doc_id}'}</h6>
                        <p className="text-secondary text-xs mb-3" style={{ lineHeight: '1.6' }}>
                          Generates vector embeddings using sentence-transformers and stores vectors in ChromaDB.
                        </p>
                      </div>
                      <div className="border-top pt-3 mt-3 d-flex align-items-center justify-content-between" style={{ borderColor: 'var(--border-gray)' }}>
                        <small className="font-monospace text-xs text-secondary">
                          Vector Count: <strong className="text-emerald">{vectorCount > 0 ? vectorCount : '0'}</strong>
                        </small>
                        {renderStepButton(4, () => executeStep4Embed(), !docId || chunkStatus !== 'success' || embedStatus === 'loading' || autoPipelineRunning, embedStatus)}
                      </div>
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        )}

        {/* TAB 3: VECTOR SEARCH TEST BENCH */}
        {activeTab === 'vector' && (
          <Row className="h-100 justify-content-center">
            <Col lg={10} xl={9} className="h-100">
              <Card className="bp-card dashboard-card h-100 text-light p-4 d-flex flex-column overflow-auto">
                <div className="border-bottom pb-3 mb-4" style={{ borderColor: 'var(--border-gray)' }}>
                  <h5 className="fw-bold font-monospace text-emerald mb-1">
                    <i className="fa-solid fa-magnifying-glass me-2"></i> Semantic Vector Search Test Bench
                  </h5>
                  <small className="text-secondary d-block">Test raw vector similarity retrieval against ChromaDB (POST /api/v1/search) without LLM answer generation.</small>
                </div>

                {/* Error Banner: Red Background with White Text */}
                {searchError && (
                  <Alert className="bp-alert-error py-2.5 px-3.5 text-xs font-monospace mb-4 rounded-3 d-flex align-items-center gap-2">
                    <i className="fa-solid fa-circle-exclamation text-white fs-5"></i>
                    <span>{searchError}</span>
                  </Alert>
                )}

                {/* Search Form */}
                <Form onSubmit={handleExecuteVectorSearch} className="mb-4">
                  <Row className="g-3 align-items-end">
                    <Col md={7}>
                      <Form.Label className="text-secondary font-monospace text-xs fw-bold">SEARCH QUERY</Form.Label>
                      <Form.Control
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="e.g., cooling fan cable disconnect procedure"
                        className="bg-dark text-light border-secondary font-sans"
                      />
                    </Col>
                    <Col md={3}>
                      <Form.Label className="text-secondary font-monospace text-xs fw-bold">TOP-K RESULTS: {searchTopK}</Form.Label>
                      <Form.Range
                        min={1}
                        max={15}
                        value={searchTopK}
                        onChange={(e) => setSearchTopK(e.target.value)}
                        className="custom-range"
                      />
                    </Col>
                    <Col md={2}>
                      <Button
                        type="submit"
                        disabled={isSearching || !searchQuery.trim()}
                        className={`${isSearching ? 'btn-working-custom' : 'btn-success-custom'} w-100 py-2 font-monospace text-xs rounded-pill`}
                      >
                        {isSearching ? (
                          <><Spinner animation="border" size="sm" style={{ color: '#ffffff' }} /> Working...</>
                        ) : (
                          <><i className="fa-solid fa-search me-1"></i> Search</>
                        )}
                      </Button>
                    </Col>
                  </Row>
                </Form>

                {/* Search Results Display */}
                <div className="flex-grow-1 overflow-auto my-4 py-2 d-flex flex-column gap-3">
                  {searchResults.length > 0 ? (
                    searchResults.map((res, idx) => (
                      <div key={idx} className="p-4 my-2 rounded-3 border shadow-sm" style={{ backgroundColor: '#070c07', borderColor: 'var(--border-gray)' }}>
                        <div className="d-flex align-items-center justify-content-between mb-3 font-monospace text-xs">
                          <div className="d-flex align-items-center gap-2">
                            <span className="badge-emerald font-monospace px-2.5 py-1">RESULT #{idx + 1}</span>
                            <span className="text-light fw-bold">Page {res.page_number}</span>
                            <small className="text-secondary">(Chunk ID: {res.chunk_id ? res.chunk_id.substring(0, 8) : 'N/A'})</small>
                          </div>
                          <Badge bg="dark" className="border border-emerald text-emerald font-monospace px-2.5 py-1">
                            Similarity: {res.score ? res.score.toFixed(3) : 'N/A'}
                          </Badge>
                        </div>
                        <div className="whitespace-pre-wrap text-light font-sans text-xs p-3 rounded-3" style={{ backgroundColor: '#0b140b', lineHeight: '1.6', border: '1px solid #162416' }}>
                          {res.text}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-5 text-secondary font-monospace text-xs">
                      <i className="fa-solid fa-vector-square fs-2 d-block mb-2 text-emerald opacity-50"></i>
                      <span>Enter a query above to execute vector search against indexed manual chunks.</span>
                    </div>
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        )}
      </Container>

      {/* Source Evidence Inspector Modal */}
      <Modal show={!!inspectedSource} onHide={() => setInspectedSource(null)} centered data-bs-theme="dark">
        <Modal.Header closeButton className="border-secondary bg-dark">
          <Modal.Title className="text-light fs-6 font-monospace d-flex align-items-center gap-2">
            <i className="fa-solid fa-book-open text-emerald"></i>
            <span>Grounded Evidence Inspector</span>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className="bg-dark text-light p-4 font-sans">
          <div className="d-flex align-items-center justify-content-between mb-3 font-monospace text-xs">
            <span className="badge-emerald">Page {inspectedSource?.page}</span>
            <span className="text-emerald">Similarity Score: {inspectedSource?.score ? inspectedSource.score.toFixed(3) : 'N/A'}</span>
          </div>

          <small className="text-secondary font-monospace d-block text-uppercase fw-bold mb-1" style={{ fontSize: '11px' }}>CHUNK ID</small>
          <div className="font-monospace text-xs text-light mb-3 p-2 rounded" style={{ backgroundColor: '#141414' }}>
            {inspectedSource?.chunk_id || 'N/A'}
          </div>

          <small className="text-secondary font-monospace d-block text-uppercase fw-bold mb-1" style={{ fontSize: '11px' }}>EVIDENCE PREVIEW CONTENT</small>
          <div className="p-3 rounded text-xs font-sans text-light" style={{ backgroundColor: '#141414', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
            {inspectedSource?.preview || 'No content snippet available.'}
          </div>

          <div className="mt-4 pt-2 border-top border-secondary d-flex justify-content-end">
            <Button onClick={() => setInspectedSource(null)} className="btn-success-custom py-1.5 px-4 font-monospace text-xs rounded-pill">
              Close Inspector
            </Button>
          </div>
        </Modal.Body>
      </Modal>
    </div>
  );
};
