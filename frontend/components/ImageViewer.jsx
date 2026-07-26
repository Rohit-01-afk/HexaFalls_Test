"use client";

import React, { useState } from 'react';
import { Card, Button, ButtonGroup, Badge } from 'react-bootstrap';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Eye,
  Layers,
  Sparkles,
  RotateCcw
} from 'lucide-react';

export const ImageViewer = ({
  manualId,
  currentPage,
  totalPages,
  onPageChange,
  activePhotoUrl,
}) => {
  const [zoom, setZoom] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const displayUrl = activePhotoUrl
    ? activePhotoUrl
    : manualId
    ? `http://localhost:8000/storage/page_images/${manualId}/page_${currentPage}.png`
    : null;

  return (
    <Card className="h-100 corp-card text-light border-secondary shadow-lg d-flex flex-column">
      {/* Header bar */}
      <Card.Header className="corp-header d-flex justify-content-between align-items-center py-3 px-4">
        <div className="d-flex align-items-center gap-2">
          <Eye size={18} className="text-info" />
          <h6 className="mb-0 fw-bold text-light text-uppercase tracking-wider font-monospace">
            Schematic Diagram Inspector
          </h6>
        </div>

        {/* Page controls */}
        {manualId && !activePhotoUrl && (
          <div className="d-flex align-items-center gap-2 bg-dark bg-opacity-75 border border-secondary px-3 py-1 rounded-pill">
            <Button
              variant="link"
              size="sm"
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              className="p-0 text-light text-decoration-none"
            >
              <ChevronLeft size={16} />
            </Button>
            <span className="font-monospace text-info font-semibold text-xs">
              Page {currentPage} / {totalPages}
            </span>
            <Button
              variant="link"
              size="sm"
              onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage >= totalPages}
              className="p-0 text-light text-decoration-none"
            >
              <ChevronRight size={16} />
            </Button>
          </div>
        )}

        {/* Zoom & Controls */}
        <ButtonGroup size="sm">
          <Button
            variant="outline-secondary"
            onClick={() => setZoom(Math.max(40, zoom - 20))}
            className="text-light border-secondary"
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </Button>
          <Button variant="outline-secondary" disabled className="text-info font-monospace fw-bold border-secondary px-2">
            {zoom}%
          </Button>
          <Button
            variant="outline-secondary"
            onClick={() => setZoom(Math.min(250, zoom + 20))}
            className="text-light border-secondary"
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </Button>
          <Button
            variant="outline-secondary"
            onClick={() => setZoom(100)}
            className="text-light border-secondary"
            title="Reset Zoom"
          >
            <RotateCcw size={14} />
          </Button>
          <Button
            variant="outline-secondary"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="text-light border-secondary"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </Button>
        </ButtonGroup>
      </Card.Header>

      {/* Main Image Display Workspace */}
      <Card.Body className="flex-grow-1 bg-dark bg-opacity-75 overflow-auto p-4 d-flex align-items-center justify-content-center blueprint-grid">
        {displayUrl ? (
          <div className="d-flex justify-content-center align-items-center w-100">
            <img
              src={displayUrl}
              alt="Schematic Blueprint"
              style={{ width: `${zoom}%`, maxWidth: 'none' }}
              className="rounded-3 border border-info border-opacity-50 shadow-lg object-fit-contain"
            />
          </div>
        ) : (
          <div className="text-center p-5 rounded-4 bg-dark bg-opacity-90 border border-secondary shadow-lg" style={{ maxWidth: '420px' }}>
            <div className="p-3 rounded-circle bg-info bg-opacity-10 text-info border border-info border-opacity-25 d-inline-flex mb-3">
              <Layers size={32} />
            </div>
            <h5 className="fw-bold text-light mb-2">High-Res Schematic HUD</h5>
            <p className="text-secondary text-xs mb-4">
              Select a page reference or upload a manual PDF/photo schematic to inspect detailed engineering blueprints with Gemini 2.5 Flash.
            </p>
            <Badge bg="dark" className="border border-info text-info font-monospace py-2 px-3 rounded-pill">
              <Sparkles size={14} className="me-1" /> Vision Fallback Active
            </Badge>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};
