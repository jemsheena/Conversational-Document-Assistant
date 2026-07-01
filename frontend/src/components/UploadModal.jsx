import { useState, useCallback } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import Modal from './Modal'

export default function UploadModal({
  files,
  setFiles,
  onUpload,
  onClose,
  isUploading,
  fileInputRef,
}) {
  const [dragActive, setDragActive] = useState(false)

  const addFiles = useCallback(
    (incoming) => {
      const pdfs = Array.from(incoming).filter((f) => f.name.endsWith('.pdf'))
      if (pdfs.length > 0) {
        setFiles((prev) => [...prev, ...pdfs])
      }
    },
    [setFiles]
  )

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    addFiles(e.dataTransfer.files)
  }

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <Modal onClose={onClose}>
      <h3 className="modal-title">Upload PDFs</h3>
      <p className="modal-subtitle">Files stay private to this chat</p>

      <div
        className={`upload-dropzone ${dragActive ? 'active' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={(e) => {
          e.preventDefault()
          setDragActive(false)
        }}
      >
        <Upload size={32} style={{ color: 'var(--accent)', margin: '0 auto' }} />
        <p>Drop PDFs here or click to browse</p>
      </div>

      {files.length > 0 && (
        <ul className="upload-file-list">
          {files.map((file, index) => (
            <li key={`${file.name}-${index}`} className="upload-file-item">
              <FileText size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
              <span className="upload-file-name">{file.name}</span>
              <button
                type="button"
                className="upload-file-remove"
                onClick={() => removeFile(index)}
                aria-label={`Remove ${file.name}`}
              >
                <X size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="modal-footer">
        <button
          type="button"
          className="upload-btn"
          disabled={files.length === 0 || isUploading}
          onClick={onUpload}
        >
          {isUploading ? 'Uploading...' : `Upload ${files.length || ''} file${files.length === 1 ? '' : 's'}`}
        </button>
        <button type="button" className="modal-close-btn" onClick={onClose}>
          Cancel
        </button>
      </div>
    </Modal>
  )
}
