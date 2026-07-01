import { useState, useRef, useEffect, useCallback } from 'react'
import Message from '../components/Message'
import Modal from '../components/Modal'
import UploadModal from '../components/UploadModal'
import {
  Send, Paperclip, FileText, Upload, Sparkles,
  Lightbulb, Search, List
} from 'lucide-react'

const SUGGESTIONS = [
  { icon: List, label: 'Summarize the key points' },
  { icon: Lightbulb, label: 'What is the main topic?' },
  { icon: Search, label: 'Explain in simple terms' },
]

export default function Chat({ chat }) {
  const {
    messages, currentResponse, isLoading, isUploading,
    activeConversation, sendMessage, uploadFiles
  } = chat

  const [input, setInput] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [showSources, setShowSources] = useState(false)
  const [sources, setSources] = useState([])
  const [showAttachments, setShowAttachments] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const textareaRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentResponse])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [input])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    const query = input
    setInput('')
    await sendMessage(query)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragActive(false)
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'))
    if (files.length > 0) {
      setSelectedFiles(files)
      setShowUpload(true)
    }
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setDragActive(false)
  }, [])

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files).filter(f => f.name.endsWith('.pdf'))
    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files])
      setShowUpload(true)
    }
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return
    try {
      await uploadFiles(selectedFiles)
      setSelectedFiles([])
      setShowUpload(false)
    } catch (err) {
      alert('Upload failed: ' + (err.message || 'Unknown error'))
    }
  }

  const handleShowSources = (src) => {
    setSources(src)
    setShowSources(true)
  }

  const handleSuggestion = (label) => {
    setInput(label)
    textareaRef.current?.focus()
  }

  const renderAttachmentBar = () => {
    const attachments = activeConversation?.uploadedFiles || []
    if (attachments.length === 0) return null

    return (
      <div className="attachments-bar">
        <button className="attachments-review-btn" onClick={() => setShowAttachments(true)}>
          {attachments.length} attachment{attachments.length !== 1 ? 's' : ''}
        </button>
        <div className="attachments-list">
          {attachments.slice(0, 4).map((name) => (
            <span key={name} className="attachment-chip" title={name}>
              {name}
            </span>
          ))}
          {attachments.length > 4 && (
            <span className="attachment-chip">+{attachments.length - 4} more</span>
          )}
        </div>
      </div>
    )
  }

  const renderInputBar = (placeholder) => (
    <div className="input-area">
      <div className="input-container">
        {renderAttachmentBar()}
        <div className="chat-input-wrapper">
          <button
            className="input-btn"
            onClick={() => setShowUpload(true)}
            title="Upload PDF"
          >
            <Paperclip size={20} />
          </button>
          <textarea
            ref={textareaRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
          />
          <div className="input-actions">
            <button
              className="input-btn send"
              disabled={!input.trim() || isLoading}
              onClick={handleSubmit}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderModals = () => (
    <>
      {showUpload && (
        <UploadModal
          files={selectedFiles}
          setFiles={setSelectedFiles}
          onUpload={handleUpload}
          onClose={() => { setShowUpload(false); setSelectedFiles([]) }}
          isUploading={isUploading}
          fileInputRef={fileInputRef}
        />
      )}

      {showSources && (
        <Modal onClose={() => setShowSources(false)} className="scrollable" align="left">
          <h3 className="modal-title">Sources</h3>
          <p className="modal-subtitle">{sources.length} reference{sources.length !== 1 ? 's' : ''} found</p>
          {sources.map((src, i) => (
            <div key={i} className="upload-file-item column">
              <strong>
                {src.doc}
                <span className="source-page-badge">Page {src.page}</span>
              </strong>
              <p>{src.snippet}</p>
            </div>
          ))}
          <div className="modal-footer">
            <button className="modal-close-btn" onClick={() => setShowSources(false)}>Close</button>
          </div>
        </Modal>
      )}

      {showAttachments && (
        <Modal onClose={() => setShowAttachments(false)} className="scrollable" align="left">
          <h3 className="modal-title">Attached files</h3>
          <p className="modal-subtitle">
            {(activeConversation?.uploadedFiles || []).length} file(s) in this chat
          </p>
          {(activeConversation?.uploadedFiles || []).map((fileName, i) => (
            <div key={`${fileName}-${i}`} className="upload-file-item">
              <FileText size={16} style={{ color: 'var(--accent)', flexShrink: 0 }} />
              <span className="upload-file-name">{fileName}</span>
            </div>
          ))}
          <div className="modal-footer">
            <button className="modal-close-btn" onClick={() => setShowAttachments(false)}>Close</button>
          </div>
        </Modal>
      )}

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".pdf"
        multiple
        hidden
      />
    </>
  )

  if (messages.length === 0 && !currentResponse) {
    return (
      <>
        <div
          className="welcome-screen"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          {dragActive && (
            <div className="welcome-drop-overlay">
              <div className="welcome-drop-card">
                <Upload size={48} style={{ color: 'var(--accent)', margin: '0 auto' }} />
                <h3>Drop your PDFs here</h3>
              </div>
            </div>
          )}

          <div className="welcome-hero">
            <div className="welcome-logo">
              <Sparkles size={28} color="white" />
            </div>
            <h1 className="welcome-title">What would you like to know?</h1>
            <p className="welcome-subtitle">
              Attach a PDF, then ask questions about it. You can also drag and drop files anywhere on this page.
            </p>
          </div>

          <div className="welcome-input">
            {renderInputBar('Ask about your documents...')}
          </div>

          <button
            type="button"
            className="welcome-upload-btn"
            onClick={() => setShowUpload(true)}
          >
            <Paperclip size={16} />
            Upload PDF
          </button>

          <div className="welcome-suggestions">
            <span className="welcome-suggestions-label">Try asking</span>
            <div className="welcome-suggestion-list">
              {SUGGESTIONS.map((suggestion) => {
                const Icon = suggestion.icon
                return (
                  <button
                    key={suggestion.label}
                    type="button"
                    className="welcome-suggestion-chip"
                    onClick={() => handleSuggestion(suggestion.label)}
                  >
                    <Icon size={15} />
                    <span>{suggestion.label}</span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {renderModals()}
      </>
    )
  }

  return (
    <>
      {isUploading && (
        <div className="processing-banner">
          <div className="typing-indicator"><span></span><span></span><span></span></div>
          Processing documents...
        </div>
      )}

      <div className="chat-messages" onDrop={handleDrop} onDragOver={handleDragOver} onDragLeave={handleDragLeave}>
        {messages.map((msg, idx) => (
          <Message
            key={idx}
            message={msg}
            onShowSources={handleShowSources}
          />
        ))}

        {currentResponse && (
          <Message
            message={{ role: 'assistant', content: currentResponse }}
            isStreaming
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {renderInputBar('Ask a question about your documents...')}
      {renderModals()}
    </>
  )
}
