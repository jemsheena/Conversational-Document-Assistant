import { FileText, User, Bot } from 'lucide-react'

export default function Message({ message, isStreaming, onShowSources }) {
  const isUser = message.role === 'user'

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      <div className="message-content">
        <div className={`message-avatar ${isUser ? 'user' : 'assistant'}`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        <div className="message-body">
          <div className="message-text">
            {message.content}

            {isStreaming && (
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            )}

            {!isStreaming && message.sources && message.sources.length > 0 && (
              <div className="message-sources">
                <button
                  className="sources-toggle"
                  onClick={() => onShowSources && onShowSources(message.sources)}
                >
                  <FileText size={14} />
                  View {message.sources.length} sources
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
