'use client'

import React, { useState, useRef, useCallback } from 'react'
import styles from '../app/page.module.css'
import { Upload, ImageIcon, X, Loader2, Search } from 'lucide-react'

interface ImageDropZoneProps {
  onAnalyze: (file: File) => void
  isAnalyzing: boolean
}

export default function ImageDropZone({ onAnalyze, isAnalyzing }: ImageDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const MAX_SIZE = 10 * 1024 * 1024 // 10 MB
  const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp']

  const validateAndSet = useCallback((file: File) => {
    setValidationError(null)

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setValidationError(`Unsupported format: ${file.type}. Use PNG, JPEG, or WebP.`)
      return
    }
    if (file.size > MAX_SIZE) {
      setValidationError(`File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max 10MB.`)
      return
    }

    setSelectedFile(file)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target?.result as string)
    reader.readAsDataURL(file)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) validateAndSet(file)
  }, [validateAndSet])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => setIsDragOver(false)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) validateAndSet(file)
  }

  const handleClear = () => {
    setSelectedFile(null)
    setPreview(null)
    setValidationError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleAnalyzeClick = () => {
    if (selectedFile) onAnalyze(selectedFile)
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`
  }

  return (
    <div className={styles.imageDropWrapper}>
      {!preview ? (
        <div
          className={`${styles.dropZone} ${isDragOver ? styles.dropZoneActive : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <Upload size={36} className={styles.dropIcon} />
          <p className={styles.dropText}>Drop image or click to upload</p>
          <span className={styles.dropHint}>PNG, JPEG, WebP • Max 10MB</span>

          {validationError && (
            <div className={styles.dropError}>{validationError}</div>
          )}
        </div>
      ) : (
        <div className={styles.imagePreviewContainer}>
          <div className={styles.imagePreviewWrapper}>
            <img src={preview} alt="Upload preview" className={styles.imagePreview} />
            {isAnalyzing && <div className={styles.imageScanOverlay}><div className={styles.imageScanLine}></div></div>}
            <button
              className={styles.clearImageButton}
              onClick={handleClear}
              disabled={isAnalyzing}
              title="Remove image"
            >
              <X size={14} />
            </button>
          </div>
          <div className={styles.imageMetaRow}>
            <span className={styles.imageFileName}>
              <ImageIcon size={12} />
              {selectedFile?.name}
            </span>
            <span className={styles.imageFileSize}>
              {selectedFile ? formatSize(selectedFile.size) : ''}
            </span>
          </div>
          <button
            className={`${styles.analyzeButton} neon-border`}
            onClick={handleAnalyzeClick}
            disabled={isAnalyzing}
            style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className={styles.spin} size={16} />
                <span>ANALYZING IMAGE...</span>
              </>
            ) : (
              <>
                <Search size={16} />
                <span>RUN IMAGE FORENSICS</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
