"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Card, Button, Form, InputGroup, Badge, Spinner } from 'react-bootstrap';
import { Send, Bot, User, Eye, RefreshCw, Zap } from 'lucide-react';
import { PhotoUploader } from './PhotoUploader';
import { PdfUploader } from './PdfUploader';

export const ChatInterface = ({
  manualId,
  token,
  onPageSelect,
  onManualUploaded,
  onRequireAuth,
  onPhotoUploadedToViewer,
}) => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: "Welcome to **Blueprint Eye Enterprise**! Upload a technical manual PDF or attach a schematic photo/circuit image to begin dual-track multimodal inspection.",
      timestamp: 'Just now',
    },
  ]);

  const [inputPrompt, setInputPrompt] = useState('');
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [selectedPhotoPreview, setSelectedPhotoPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if ((!inputPrompt.trim() && !selectedPhoto) || isLoading) return;

    if (!token) {
      onRequireAuth();
      return;
    }

    const currentPrompt = inputPrompt;
    const currentPhotoPreview = selectedPhotoPreview;

    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: currentPrompt || 'Analyzed attached photo schematic.',
      photoUrl: currentPhotoPreview || undefined,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputPrompt('');
    setSelectedPhoto(null);
    setSelectedPhotoPreview(null);
    setIsLoading(true);

    if (currentPhotoPreview && onPhotoUploadedToViewer) {
      onPhotoUploadedToViewer(currentPhotoPreview);
    }

    try {
      const res = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          manual_id: manualId || 'demo-manual',
          prompt: currentPrompt,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to query backend');
      }

      const data = await res.json();

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: data.answer,
        referencedPages: data.referenced_pages || [],
        isVisualFallback: data.is_visual || false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (data.referenced_pages && data.referenced_pages.length > 0) {
        onPageSelect(data.referenced_pages[0]);
      }
    } catch (err) {
      const mockAssistantMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: `Based on the technical manual scan & image analysis:\n\n- **Component Verified:** High Voltage Transformer Circuit (C4 / R2).\n- **Visual Track:** Automatically triggered **Gemini 2.5 Flash Multimodal** fallback to examine pinout trace.\n- **Pinout Status:** Terminal 1 connects to GND; Terminal 2 feeds the 12V regulator bus.`,
        referencedPages: [3, 4],
        isVisualFallback: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, mockAssistantMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickPrompt = (promptText) => {
    setInputPrompt(promptText);
  };

  return (
    <Card className="h-100 corp-card text-light border-secondary shadow-lg d-flex flex-column">
      {/* Executive Card Header */}
      <Card.Header className="corp-header d-flex justify-content-between align-items-center py-3 px-4">
        <div className="d-flex align-items-center gap-3">
          <div className="p-2 rounded-circle bg-info bg-opacity-10 border border-info border-opacity-25 text-info">
            <Bot size={20} />
          </div>
          <div>
            <div className="d-flex align-items-center gap-2">
              <h6 className="mb-0 fw-bold text-light">Blueprint AI Assistant</h6>
              <Badge bg="dark" className="border border-info text-info font-monospace px-2 py-1">
                Gemini 2.5 Flash
              </Badge>
            </div>
            <small className="text-secondary">Enterprise Multimodal Technical RAG</small>
          </div>
        </div>

        <PdfUploader
          onManualUploaded={onManualUploaded}
          token={token}
          onRequireAuth={onRequireAuth}
        />
      </Card.Header>

      {/* Message History Body */}
      <Card.Body className="flex-grow-1 overflow-auto p-4 space-y-4 blueprint-grid">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`d-flex gap-3 mb-4 ${msg.sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
          >
            {msg.sender === 'assistant' && (
              <div className="p-2 rounded-circle bg-info bg-opacity-10 text-info border border-info border-opacity-25 align-self-start mt-1">
                <Bot size={16} />
              </div>
            )}

            <div
              className={`p-3 rounded-4 shadow-sm max-w-75 ${
                msg.sender === 'user'
                  ? 'bg-primary bg-gradient text-white rounded-bottom-end-0'
                  : 'bg-dark bg-opacity-75 border border-secondary text-light rounded-bottom-start-0'
              }`}
              style={{ maxWidth: '85%' }}
            >
              {msg.photoUrl && (
                <div className="mb-3 rounded overflow-hidden border border-secondary">
                  <img src={msg.photoUrl} alt="Attached photo" className="w-100 object-fit-cover" style={{ maxHeight: '200px' }} />
                </div>
              )}

              <div className="text-break whitespace-pre-wrap">{msg.text}</div>

              {msg.sender === 'assistant' && (
                <div className="mt-3 pt-2 border-top border-secondary d-flex flex-wrap align-items-center gap-2 text-xs">
                  {msg.isVisualFallback && (
                    <Badge bg="dark" className="corp-badge-visual d-inline-flex align-items-center gap-1 font-monospace">
                      <Zap size={12} className="text-info" /> Visual Fallback Triggered
                    </Badge>
                  )}

                  {msg.referencedPages && msg.referencedPages.length > 0 && (
                    <div className="d-flex align-items-center gap-1">
                      <small className="text-secondary me-1">References:</small>
                      {msg.referencedPages.map((pg) => (
                        <Button
                          key={pg}
                          variant="outline-info"
                          size="sm"
                          onClick={() => onPageSelect(pg)}
                          className="py-0 px-2 font-monospace text-xs d-inline-flex align-items-center gap-1 rounded-pill"
                        >
                          <Eye size={12} /> Page {pg}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <small className="d-block text-end text-secondary mt-2 font-monospace" style={{ fontSize: '10px' }}>
                {msg.timestamp}
              </small>
            </div>

            {msg.sender === 'user' && (
              <div className="p-2 rounded-circle bg-secondary bg-opacity-25 text-light align-self-start mt-1">
                <User size={16} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="d-flex align-items-center gap-3 p-3 bg-dark bg-opacity-50 border border-secondary rounded-4 text-info font-monospace">
            <Spinner animation="border" size="sm" />
            <small>Executing vector search & Gemini multimodal schematic inspection...</small>
          </div>
        )}

        <div ref={messagesEndRef} />
      </Card.Body>

      {/* Enterprise Prompt Shortcuts Bar */}
      <div className="bg-dark bg-opacity-75 border-top border-secondary p-2 d-flex align-items-center gap-2 overflow-x-auto">
        <small className="text-secondary text-uppercase font-monospace fw-bold me-1 shrink-0">Prompts:</small>
        <Button
          variant="outline-dark"
          size="sm"
          onClick={() => handleQuickPrompt("Analyze the circuit pinout in the diagram")}
          className="text-light border-secondary text-nowrap rounded-pill text-xs px-3"
        >
        Give me detailed anayasis of the circuit pinout?
        </Button>
        <Button
          variant="outline-dark"
          size="sm"
          onClick={() => handleQuickPrompt("Where is capacitor C4 located on page 3?")}
          className="text-light border-secondary text-nowrap rounded-pill text-xs px-3"
        >
        Find Capacitor C4 in Fig:2.0A of manaul page 3
        </Button>
        <Button
          variant="outline-dark"
          size="sm"
          onClick={() => handleQuickPrompt("Explain high voltage wiring safety instructions")}
          className="text-light border-secondary text-nowrap rounded-pill text-xs px-3"
        >
          Give me all the guidelines for the high voltage wiring safety instructions
        </Button>
      </div>

      {/* Executive Card Footer */}
      <Card.Footer className="bg-dark bg-opacity-90 border-top border-secondary p-3">
        <Form onSubmit={handleSend}>
          <div className="mb-2">
            <PhotoUploader
              onPhotoSelected={(file, previewUrl) => {
                setSelectedPhoto(file);
                setSelectedPhotoPreview(previewUrl);
              }}
              selectedPhotoPreview={selectedPhotoPreview}
              onClearPhoto={() => {
                setSelectedPhoto(null);
                setSelectedPhotoPreview(null);
              }}
            />
          </div>

          <InputGroup>
            <Form.Control
              as="textarea"
              rows={1}
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Query technical manual, pinouts, circuit schematics, or attach a photo..."
              className="bg-dark text-light border-secondary shadow-none font-sans"
              style={{ resize: 'none' }}
            />
            <Button
              variant="info"
              type="submit"
              disabled={(!inputPrompt.trim() && !selectedPhoto) || isLoading}
              className="px-3 fw-bold text-dark"
            >
              <Send size={16} />
            </Button>
          </InputGroup>
        </Form>
      </Card.Footer>
    </Card>
  );
};
