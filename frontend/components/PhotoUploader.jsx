"use client";

import React, { useRef } from 'react';
import { Button, Badge } from 'react-bootstrap';
import { Camera, X } from 'lucide-react';

export const PhotoUploader = ({ onPhotoSelected, selectedPhotoPreview, onClearPhoto }) => {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onPhotoSelected(file, reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="d-flex align-items-center gap-2">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/*"
        className="d-none"
      />

      {selectedPhotoPreview ? (
        <Badge bg="dark" className="border border-info text-info d-flex align-items-center gap-2 py-1.5 px-2.5 rounded-pill">
          <img src={selectedPhotoPreview} alt="Attached preview" className="rounded" style={{ width: '20px', height: '20px', objectFit: 'cover' }} />
          <span className="text-truncate max-w-100 font-monospace text-light" style={{ maxWidth: '120px' }}>Photo Attached</span>
          <Button
            variant="link"
            size="sm"
            onClick={onClearPhoto}
            className="p-0 text-danger text-decoration-none ms-1"
          >
            <X size={14} />
          </Button>
        </Badge>
      ) : (
        <Button
          variant="outline-secondary"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          className="d-flex align-items-center gap-1.5 text-light border-secondary rounded-pill px-3"
          title="Attach circuit photo or schematic scan"
        >
          <Camera size={14} className="text-info" />
          <span>Attach Photo</span>
        </Button>
      )}
    </div>
  );
};
