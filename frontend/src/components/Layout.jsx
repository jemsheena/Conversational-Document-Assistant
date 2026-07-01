import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store/useAuth.jsx'
import {
  Plus, MessageSquare, LogOut, Pencil, Pin, PinOff, Eraser, Sparkles, Menu, User
} from 'lucide-react'
import { useState } from 'react'

export default function Layout({
  children,
  conversations,
  activeConv,
  onNewChat,
  onSelectConv,
  onRenameConv,
  onTogglePinConv,
  onClearConv,
}) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const sortedConversations = [...conversations].sort((a, b) => {
    if (a.pinned === b.pinned) return 0
    return a.pinned ? -1 : 1
  })

  const handleLogout = () => {
    logout()
    navigate('/auth')
  }

  const handleNewChat = () => {
    onNewChat()
    setSidebarOpen(false)
  }

  const handleSelectConv = (id) => {
    onSelectConv(id)
    setSidebarOpen(false)
  }

  return (
    <div className="app-layout">
      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="app-logo">
            <div className="app-logo-icon">
              <Sparkles size={18} color="white" />
            </div>
            <div>
              <div className="app-logo-text">Doc Assistant</div>
              <div className="app-logo-sub">RAG-powered chat</div>
            </div>
          </div>
          <button className="new-chat-btn" onClick={handleNewChat}>
            <Plus size={18} />
            <span>New chat</span>
          </button>
        </div>

        <div className="sidebar-section-label">Conversations</div>

        <div className="sidebar-conversations">
          {sortedConversations.map((conv) => (
            <div
              key={conv.id}
              className={`conv-item ${activeConv === conv.id ? 'active' : ''} ${conv.pinned ? 'pinned' : ''}`}
              onClick={() => handleSelectConv(conv.id)}
            >
              <MessageSquare size={16} />
              <span className="conv-title">{conv.title || 'New conversation'}</span>
              <div className="conv-actions">
                <button
                  className="conv-action-btn"
                  title={conv.pinned ? 'Unpin conversation' : 'Pin conversation'}
                  onClick={(e) => {
                    e.stopPropagation()
                    onTogglePinConv?.(conv.id)
                  }}
                >
                  {conv.pinned ? <PinOff size={13} /> : <Pin size={13} />}
                </button>
                <button
                  className="conv-action-btn"
                  title="Rename conversation"
                  onClick={(e) => {
                    e.stopPropagation()
                    const nextName = window.prompt('Rename conversation', conv.title || '')
                    if (nextName !== null) {
                      onRenameConv?.(conv.id, nextName)
                    }
                  }}
                >
                  <Pencil size={13} />
                </button>
                <button
                  className="conv-action-btn"
                  title="Delete conversation"
                  onClick={(e) => {
                    e.stopPropagation()
                    onClearConv?.(conv.id)
                  }}
                >
                  <Eraser size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-user" onClick={handleLogout}>
            <div className="user-avatar">
              <User size={14} />
            </div>
            <span>Log out</span>
            <LogOut size={16} className="logout-icon" />
          </div>
        </div>
      </aside>

      <div className="chat-area">
        <div className="chat-topbar">
          <button
            className="mobile-menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <span className="chat-topbar-title">Document Assistant</span>
        </div>
        {children}
      </div>
    </div>
  )
}
