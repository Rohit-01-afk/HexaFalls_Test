"use client";

import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Form, Badge, InputGroup, Modal, Alert } from 'react-bootstrap';

export const BrandIconSvg = ({ size = 32 }) => (
  <svg
    className="brand-icon-svg"
    width={size}
    height={size}
    viewBox="-5.04 -5.04 34.08 34.08"
    xmlSpace="preserve"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <g id="Free_Icons">
      <g stroke="#54c750" fill="none" strokeWidth="1.2" strokeLinejoin="round" strokeMiterlimit="10">
        <polygon points="6,21.5 0.5,12 6,2.5 18,2.5 23.5,12 18,21.5"></polygon>
        <polygon points="23.5,12 16,7.5 6,2.5 5,13.5 6,21.5 16.5,19.5"></polygon>
        <polygon points="16,7.5 5,13.5 16.5,19.5"></polygon>
        <line x1="18" y1="21.5" x2="16.5" y2="19.5"></line>
        <line x1="0.5" y1="12" x2="5" y2="13.5"></line>
        <line x1="18" y1="2.5" x2="16" y2="7.5"></line>
      </g>
    </g>
  </svg>
);

export const CapabilityTopSvg = ({ size = 48 }) => (
  <svg
    fill="#54c750"
    version="1.1"
    width={size}
    height={size}
    viewBox="0 0 45.054 45.055"
    xmlSpace="preserve"
    className="mb-3 d-inline-block"
    style={{ filter: 'drop-shadow(0 0 10px rgba(84, 199, 80, 0.5))' }}
  >
    <g id="SVGRepo_bgCarrier" strokeWidth="0"></g>
    <g id="SVGRepo_tracerCarrier" strokeLinecap="round" strokeLinejoin="round"></g>
    <g id="SVGRepo_iconCarrier">
      <g>
        <g>
          <path d="M8.527,21.027c-0.219,0.127-0.555,0.341-0.551,0.642c0.049,4.14,4.578,9.036,6.626,12.461 c1.611,2.696,3.223,5.392,4.834,8.087c0.655,1.095,1.388,2.955,3.004,2.832c3.208-0.244,5.763-7.408,7.042-9.548 c1.76-2.941,3.519-5.883,5.276-8.825c1.028-1.72,2.297-3.137,2.32-5.156c0.002-0.191-0.057-0.379-0.234-0.482 c-2.138-1.245-4.693-0.81-7.134-0.765c-1.228-0.771-0.485-5.647-0.485-6.79c0-3.416,0-6.831,0-10.247 c0-4.723-7.44-2.883-10.63-2.883c-4.619,0-2.765,8.563-2.765,11.335c0,2.767,0,5.534,0,8.301 C15.829,20.146,9.7,20.344,8.527,21.027z M34.411,23.741c0.196-0.52,0.398-1.034,0.604-1.55c0.152,0.153,0.188,0.348,0.075,0.591 c-0.058,0.108-0.118,0.219-0.177,0.328c-0.203,0.339-0.406,0.678-0.608,1.017C34.292,24.098,34.321,23.977,34.411,23.741z M12.007,25.98c-0.217-0.362-0.434-0.726-0.65-1.088c-0.207-0.347-0.403-0.659-0.579-0.947c0.454-0.708,0.908-1.416,1.367-2.121 c0.03-0.046,0.033-0.085,0.053-0.129c0.047,0,0.087-0.003,0.136-0.003c0.943,0,1.725-0.024,2.372-0.095 c-0.052,0.076-0.104,0.151-0.157,0.235c-0.801,1.276-1.594,2.554-2.364,3.844C12.125,25.778,12.066,25.88,12.007,25.98z M14.193,29.64c4.369-7.128,8.714-14.268,13.094-21.388c-0.012,0.257-0.02,0.441-0.02,0.511c0,0.261-0.02,0.596-0.046,0.963 c-2.867,5.596-5.779,11.167-8.82,16.661c-0.994,1.773-1.986,3.536-3.008,5.259C14.993,30.976,14.593,30.308,14.193,29.64z M16.629,33.714c3.246-4.919,6.486-9.844,9.744-14.755c0.306-0.46,0.377-0.422,0.15,0.082c-0.47,1.052-0.964,2.092-1.482,3.12 c-2.512,4.25-5.085,8.461-7.797,12.582C17.038,34.399,16.833,34.056,16.629,33.714z M30.044,29.923 c-0.362,1.032-0.729,2.062-1.096,3.091c-0.022,0.063-0.057,0.141-0.083,0.21c-0.884,1.479-1.768,2.955-2.65,4.433 c-0.539,0.803-1.086,1.604-1.651,2.4c-0.318,0.451-0.376,0.416-0.121-0.073c1.36-2.613,2.737-5.22,4.16-7.805 c0.428-0.774,0.856-1.551,1.285-2.326C30.157,29.37,30.227,29.402,30.044,29.923z M27.727,21.157 c0.041-0.071,0.074-0.146,0.104-0.22c0.235,0.31,0.513,0.558,0.856,0.701c0.135,0.055,0.285,0.067,0.438,0.051 c0.013,0,0.021,0.005,0.034,0.005c0.385,0,1.795-0.103,3.152-0.068c-0.065,0.072-0.137,0.143-0.184,0.222 c-3.782,6.367-7.479,12.782-11.106,19.239c-0.06-0.114-0.11-0.207-0.146-0.266c-0.862-1.442-1.724-2.885-2.586-4.326 c3.362-4.742,6.52-9.613,9.108-14.772C27.508,21.533,27.619,21.346,27.727,21.157z M27.367,4.563 c0.001,0.066,0.002,0.134,0.002,0.201c-0.022,0.03-0.041,0.042-0.064,0.078c-0.457,0.735-0.915,1.468-1.37,2.204 c-0.291,0.469-0.294,0.469-0.01-0.005c0.479-0.803,0.952-1.611,1.415-2.423C27.349,4.602,27.357,4.581,27.367,4.563z M26.177,1.883c0.032-0.042,0.059-0.078,0.088-0.118c0.188,0,0.376,0,0.564,0c0.006,0,0.011,0.008,0.018,0.009 c-0.073,0.081-0.144,0.169-0.198,0.272c-2.67,5.054-5.767,9.882-8.865,14.706c0.001-0.192,0.004-0.38,0.004-0.586 c0-0.914,0-1.827,0-2.741C20.498,9.515,23.287,5.659,26.177,1.883z M22.493,1.765c0.565,0,1.129,0,1.693,0 c-0.027,0.03-0.064,0.057-0.089,0.088c-1.41,1.845-2.801,3.705-4.171,5.579c-0.326,0.446-0.383,0.41-0.133-0.083 c0.908-1.784,1.792-3.579,2.65-5.386C22.477,1.893,22.479,1.831,22.493,1.765z M18.988,1.765c0.483,0,0.967,0,1.451,0 c-0.048,0.066-0.105,0.129-0.139,0.2c-0.812,1.72-1.656,3.426-2.514,5.125c0-0.103,0-0.206,0-0.308 C17.787,5.226,16.957,1.765,18.988,1.765z M16.385,22.202c2.476-4.035,5.091-7.984,7.596-11.995 c0.293-0.468,0.294-0.468,0.006,0.003c-3.619,5.892-7.223,11.792-10.834,17.689c-0.03-0.051-0.061-0.102-0.091-0.151 C14.157,25.89,15.259,24.037,16.385,22.202z"></path>
        </g>
      </g>
    </g>
  </svg>
);

export const LandingPage = ({ onLaunchDashboard, isAuthenticated, onLoginSuccess, onSignOut }) => {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('signin'); // 'signin' | 'signup'
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState('');

  // Selected Capability Modal State
  const [selectedCapability, setSelectedCapability] = useState(null);

  const capabilitiesData = [
    {
      id: 1,
      step: 'STEP 01',
      title: '1. Manual & Photo Ingestion',
      icon: 'fa-solid fa-file-arrow-up',
      shortDesc: 'Drag & drop technical manual PDFs or upload high-res schematic photos directly into the processing pipeline.',
      fullDetails: `BluePrint Ai features an automated ingestion engine powered by PyMuPDF and pdf2image. 
      When a user uploads a PDF technical manual or schematic photo capture, the system concurrently extracts clean text blocks for vector embeddings while rendering 200-300 DPI high-resolution page scans into local assets.
      This dual processing guarantees that no circuit pinouts or wiring details are stripped away during extraction.`
    },
    {
      id: 2,
      step: 'STEP 02',
      title: '2. Dual-Track Document Pipeline',
      icon: 'fa-solid fa-diagram-project',
      shortDesc: 'Text chunks are indexed in ChromaDB with exact page_number metadata while high-res scans are stored locally.',
      fullDetails: `The Dual-Track Architecture stores text chunks into ChromaDB (embedded vector mode) with strict metadata binding, including Document ID, Page Number, and Chunk ID.
      This allows instant Top-K vector retrieval while maintaining exact page-level traceability so that every answer returned by the AI can be visually verified against original manual scans.`
    },
    {
      id: 3,
      step: 'STEP 03',
      title: '3. Multimodal Vision Fallback',
      icon: 'fa-solid fa-brain',
      shortDesc: 'Queries with visual intent (e.g. pinouts, schematics) automatically pull page scans and query Google Gemini 2.5 Flash.',
      fullDetails: `Our backend Intent Router evaluates user prompts for visual keywords (e.g., "diagram", "schematic", "pinout", "wire", "drawing") or low vector search confidence thresholds.
      When visual intent is detected, the engine retrieves the exact high-resolution page scan and feeds both the visual scan and prompt into the modern google-genai SDK powered by Gemini 2.5 Flash.`
    }
  ];

  // Pre-configured UI test credentials
  const TEST_USER = 'admin';
  const TEST_PASS = 'blueprint123';

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenAuth = (mode) => {
    setAuthMode(mode);
    setErrorMsg(null);
    setShowAuthModal(true);
  };

  const handleFillDemoCreds = () => {
    setUsername(TEST_USER);
    setPassword(TEST_PASS);
    if (authMode === 'signup') {
      setEmail('admin@blueprint.ai');
    }
    setErrorMsg(null);
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const endpoint = authMode === 'signup' ? '/api/auth/register' : '/api/auth/token';
      const body = authMode === 'signup'
        ? JSON.stringify({ username, email, password })
        : new URLSearchParams({ username, password });

      const headers = authMode === 'signup'
        ? { 'Content-Type': 'application/json' }
        : { 'Content-Type': 'application/x-www-form-urlencoded' };

      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers,
        body,
      });

      if (res.ok) {
        const data = await res.json();
        onLoginSuccess(data.access_token, username);
        setShowAuthModal(false);
        return;
      }
    } catch (err) {
      // Backend fallback to UI testing
    }

    if (username.trim() && password.trim()) {
      onLoginSuccess('ui-test-jwt-token-2026', username);
      setShowAuthModal(false);
    } else {
      setErrorMsg('Please enter a username and password to test the UI.');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-vh-100 d-flex flex-column" style={{ backgroundColor: 'var(--bg-deep)' }}>
      {/* Navbar */}
      <nav className="navbar navbar-expand-lg sticky-top bp-nav px-4 py-3">
        <Container>
          <a className="navbar-brand d-flex align-items-center gap-2 font-monospace text-light" href="#">
            <BrandIconSvg size={32} />
            <span className="brand-title-text text-light">BluePrint <span className="text-emerald">Ai</span></span>
          </a>

          <div className="d-flex align-items-center gap-3 ms-auto">
            {isAuthenticated ? (
              <>
                <Button
                  onClick={onLaunchDashboard}
                  className="btn-nav-white"
                >
                  <i className="fa-solid fa-gauge-high"></i>
                  <span>Dashboard</span>
                </Button>
                <Button
                  onClick={onSignOut}
                  className="btn-nav-white"
                >
                  <i className="fa-solid fa-right-from-bracket"></i>
                  <span>Sign Out</span>
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={() => handleOpenAuth('signin')}
                  className="btn-nav-white"
                >
                  <i className="fa-solid fa-right-to-bracket"></i>
                  <span>Sign In</span>
                </Button>
                <Button
                  onClick={() => handleOpenAuth('signup')}
                  className="btn-nav-white"
                >
                  <i className="fa-solid fa-user-plus"></i>
                  <span>Sign Up</span>
                </Button>
              </>
            )}
            <a href="#contact" className="btn-nav-white text-decoration-none">
              <i className="fa-solid fa-envelope"></i>
              <span>Contact Us</span>
            </a>
          </div>
        </Container>
      </nav>

      {/* Hero Section with Custom Blueprint Grid Pattern & Bottom Texture Fade */}
      <section className="py-5 hero-blueprint-bg overflow-hidden">
        <Container className="py-4 position-relative" style={{ zIndex: 2 }}>
          <Row className="align-items-center g-5">
            <Col lg={6}>
              <span className="badge-emerald mb-3 d-inline-flex align-items-center gap-2">
                <i className="fa-solid fa-bolt text-emerald"></i> Multimodal Technical RAG Engine
              </span>

              <h1 className="display-4 fw-extrabold text-light mb-4" style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}>
                Solving the Visual Document Gap in <span className="text-emerald">Technical Manuals & Schematics</span>
              </h1>

              <p className="lead text-secondary mb-4" style={{ fontSize: '1.05rem' }}>
                Standard RAG platforms strip out circuit diagrams, wire pinouts, and engineering schematics during PDF text extraction. 
                <strong className="text-light"> BluePrint Ai</strong> introduces a Dual-Track Architecture combining fast vector search with high-resolution page scan fallback powered by Google Gemini.
              </p>

              <div className="d-flex flex-wrap gap-3 mb-4">
                <Button
                  onClick={onLaunchDashboard}
                  className="btn-hero-green"
                >
                  <i className="fa-solid fa-robot"></i>
                  <span> Try Our Chatbot</span>
                </Button>
              </div>

              <div className="d-flex align-items-center gap-4 text-secondary text-xs">
                <span><i className="fa-solid fa-check text-emerald me-1"></i> 200-300 DPI Rendering</span>
                <span><i className="fa-solid fa-check text-emerald me-1"></i> Gemini 2.5 Flash</span>
                <span><i className="fa-solid fa-check text-emerald me-1"></i> Dual-Track Pipeline</span>
              </div>
            </Col>

            {/* Hero Image Section with Pointed SVG Arrow Overlay */}
            <Col lg={6}>
              <div className="position-relative">
                <svg
                  className="custom-pointed-arrow d-none d-md-block"
                  xmlns="http://www.w3.org/2000/svg"
                  version="1.1"
                  viewBox="0 0 640 800"
                >
                  <g
                    strokeWidth="17"
                    stroke="#54c750"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray="4.5 0"
                    transform="matrix(0.9781476007338057,0.20791169081775931,-0.20791169081775931,0.9781476007338057,14.157444092285914,-115.79078135520524)"
                  >
                    <path d="M97.5 177.5Q589.5 332.5 320 400Q97.5 442.5 542.5 622.5 " markerEnd="url(#SvgjsMarkerBrandGreen)"></path>
                  </g>
                  <defs>
                    <marker
                      markerWidth="10"
                      markerHeight="10"
                      refX="5"
                      refY="5"
                      viewBox="0 0 10 10"
                      orient="auto"
                      id="SvgjsMarkerBrandGreen"
                    >
                      <polyline
                        points="0,5 5,2.5 0,0"
                        fill="none"
                        strokeWidth="1.6666666666666667"
                        stroke="#54c750"
                        strokeLinecap="round"
                        transform="matrix(1,0,0,1,1.6666666666666667,2.5)"
                        strokeLinejoin="round"
                      ></polyline>
                    </marker>
                  </defs>
                </svg>

                <div className="bp-card p-3 shadow-lg border border-secondary">
                  <img
                    src="/hero_schematic.png"
                    alt="BluePrint Ai Technical Schematic Analysis"
                    className="w-100 rounded object-fit-cover shadow"
                    style={{ maxHeight: '420px', border: '1px solid var(--border-gray)' }}
                  />
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Technical Capabilities & Procedure Section */}
      <section id="capabilities" className="py-5 position-relative" style={{ backgroundColor: 'var(--bg-deep)' }}>
        <Container className="py-3 position-relative" style={{ zIndex: 2 }}>
          {/* Section Header & Brand Green Capability Top SVG */}
          <div className="text-center max-w-2xl mx-auto mb-5">
            <CapabilityTopSvg size={52} />
            <br />
            <span className="badge-emerald mb-2 d-inline-block">Technical Capabilities & Architecture</span>
            <h2 className="fw-bold text-light display-6 mb-3">How BluePrint Ai Operates</h2>
            <p className="text-secondary lead fs-6 max-w-xl mx-auto" style={{ maxWidth: '680px' }}>
              BluePrint Ai seamlessly unifies vector text retrieval with high-resolution vision inspection fallback. 
              Explore our three core architectural steps below — hover over each card to reveal details, and click "Know More" to access full technical specifications.
            </p>
          </div>

          {/* Interactive Expandable Cards Grid */}
          <Row className="g-4">
            {capabilitiesData.map((cap) => (
              <Col md={4} key={cap.id}>
                <div className="bp-card capability-card d-flex flex-column justify-content-between h-100">
                  {/* Card Visible Header: Square Icon Box & Title */}
                  <div>
                    <div className="d-flex align-items-center justify-content-between mb-3">
                      <div className="capability-icon-box">
                        <i className={cap.icon}></i>
                      </div>
                      <span className="font-monospace text-emerald text-xs fw-bold px-2 py-1 bg-emerald bg-opacity-10 rounded">
                        {cap.step}
                      </span>
                    </div>

                    <h5 className="fw-bold text-light mb-2 fs-5">{cap.title}</h5>
                  </div>

                  {/* Card Hidden Content (Reveals on Hover) */}
                  <div className="card-hidden-content">
                    <p className="text-secondary text-sm mb-3" style={{ lineHeight: '1.6' }}>
                      {cap.shortDesc}
                    </p>

                    <Button
                      onClick={() => setSelectedCapability(cap)}
                      className="btn-know-more w-100 font-monospace text-xs py-2 fw-bold"
                    >
                      <i className="fa-solid fa-circle-info"></i>
                      <span>Know More</span>
                    </Button>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </Container>
      </section>

      {/* Footer Section */}
      <footer id="contact" className="mt-auto py-4 footer-blueprint-bg position-relative overflow-hidden">
        <Container className="position-relative" style={{ zIndex: 2 }}>
          <Row className="align-items-center g-3">
            <Col md={4}>
              <div className="d-flex align-items-center gap-2 font-monospace text-light mb-1">
                <BrandIconSvg size={26} />
                <span className="fw-bold fs-5">BluePrint Ai</span>
              </div>
              <small className="text-secondary d-block">
                © 2026 BluePrint Ai. All rights reserved.
              </small>
            </Col>

            <Col md={4} className="text-center">
              <div className="font-monospace text-emerald text-sm mb-1">
                <i className="fa-regular fa-clock me-1"></i>
                <span>{currentTime || '2026-07-25 23:13:58'}</span>
              </div>
              <div className="font-monospace text-secondary text-sm">
                <span>Made with</span>
                <i className="fa-solid fa-heart text-white mx-1"></i>
                <span>by Team <strong className="text-emerald">KIT-KAT</strong></span>
              </div>
            </Col>

            <Col md={4} className="text-md-end">
              <div className="d-flex justify-content-md-end gap-3 text-xs">
                <a href="#contact" className="text-secondary text-decoration-none hover-emerald">Inquiry</a>
                <span className="text-secondary">•</span>
                <a href="#" className="text-secondary text-decoration-none hover-emerald">Terms of Service</a>
                <span className="text-secondary">•</span>
                <a href="#" className="text-secondary text-decoration-none hover-emerald">Privacy Policy</a>
              </div>
            </Col>
          </Row>
        </Container>
      </footer>

      {/* Capability "Know More" Detailed Specification Modal */}
      <Modal
        show={!!selectedCapability}
        onHide={() => setSelectedCapability(null)}
        centered
        data-bs-theme="dark"
      >
        <Modal.Header closeButton className="border-secondary bg-dark">
          <Modal.Title className="text-light fs-6 font-monospace d-flex align-items-center gap-2">
            <i className="fa-solid fa-microchip text-emerald"></i>
            <span>{selectedCapability?.title}</span>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className="bg-dark text-light p-4">
          <div className="d-flex align-items-center gap-3 mb-3">
            <div className="capability-icon-box">
              <i className={selectedCapability?.icon}></i>
            </div>
            <div>
              <span className="badge-emerald font-monospace">{selectedCapability?.step}</span>
              <h5 className="fw-bold text-light mb-0 mt-1">{selectedCapability?.title}</h5>
            </div>
          </div>

          <hr className="border-secondary my-3" />

          <p className="text-secondary font-sans text-sm" style={{ lineHeight: '1.7', whiteSpace: 'pre-line' }}>
            {selectedCapability?.fullDetails}
          </p>

          <div className="mt-4 pt-2 border-top border-secondary d-flex justify-content-end">
            <Button
              onClick={() => setSelectedCapability(null)}
              className="btn-hero-green py-2 px-4 font-monospace text-xs"
            >
              Close Details
            </Button>
          </div>
        </Modal.Body>
      </Modal>

      {/* Auth Modal Dialog */}
      <Modal show={showAuthModal} onHide={() => setShowAuthModal(false)} centered data-bs-theme="dark">
        <Modal.Header closeButton className="border-secondary bg-dark">
          <Modal.Title className="text-light fs-6 font-monospace d-flex align-items-center gap-2">
            <i className="fa-solid fa-lock text-emerald"></i>
            <span>{authMode === 'signup' ? 'Create BluePrint Ai Account' : 'Sign In to BluePrint Ai'}</span>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body className="bg-dark text-light p-4">
          <Alert variant="dark" className="border border-emerald bg-emerald bg-opacity-10 text-light p-3 mb-3 rounded">
            <div className="d-flex align-items-center justify-content-between mb-1">
              <span className="fw-bold font-monospace text-emerald">
                <i className="fa-solid fa-flask me-1"></i> UI Testing Credentials
              </span>
              <Button
                variant="emerald"
                size="sm"
                onClick={handleFillDemoCreds}
                className="btn-emerald py-0 px-2 text-xs font-monospace"
              >
                Auto-Fill
              </Button>
            </div>
            <div className="font-monospace text-xs text-light opacity-90">
              <div>Username: <strong className="text-emerald">{TEST_USER}</strong></div>
              <div>Password: <strong className="text-emerald">{TEST_PASS}</strong></div>
            </div>
          </Alert>

          {errorMsg && (
            <Alert variant="danger" className="py-2 text-xs font-monospace">
              {errorMsg}
            </Alert>
          )}

          <Form onSubmit={handleAuthSubmit}>
            <Form.Group className="mb-3">
              <Form.Label className="text-secondary text-xs fw-bold font-monospace">USERNAME</Form.Label>
              <InputGroup>
                <InputGroup.Text className="bg-dark border-secondary text-secondary">
                  <i className="fa-solid fa-user"></i>
                </InputGroup.Text>
                <Form.Control
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  className="bg-dark text-light border-secondary font-monospace"
                />
              </InputGroup>
            </Form.Group>

            {authMode === 'signup' && (
              <Form.Group className="mb-3">
                <Form.Label className="text-secondary text-xs fw-bold font-monospace">EMAIL ADDRESS</Form.Label>
                <InputGroup>
                  <InputGroup.Text className="bg-dark border-secondary text-secondary">
                    <i className="fa-solid fa-envelope"></i>
                  </InputGroup.Text>
                  <Form.Control
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@blueprint.ai"
                    className="bg-dark text-light border-secondary font-monospace"
                  />
                </InputGroup>
              </Form.Group>
            )}

            <Form.Group className="mb-4">
              <Form.Label className="text-secondary text-xs fw-bold font-monospace">PASSWORD</Form.Label>
              <InputGroup>
                <InputGroup.Text className="bg-dark border-secondary text-secondary">
                  <i className="fa-solid fa-key"></i>
                </InputGroup.Text>
                <Form.Control
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="blueprint123"
                  className="bg-dark text-light border-secondary font-monospace"
                />
              </InputGroup>
            </Form.Group>

            <Button variant="emerald" type="submit" disabled={isLoading} className="btn-emerald w-100 py-2 font-bold">
              {isLoading ? 'Processing...' : authMode === 'signup' ? 'Register & Open Dashboard' : 'Sign In & Open Dashboard'}
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
    </div>
  );
};
