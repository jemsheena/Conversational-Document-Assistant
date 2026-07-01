import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Chat from './pages/Chat'
import Auth from './pages/Auth'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './store/useAuth.jsx'
import { useChat } from './store/useChat.jsx'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? <>{children}</> : <Navigate to="/auth" />
}

function ProtectedApp() {
  const chat = useChat()

  return (
    <Layout
      conversations={chat.conversations}
      activeConv={chat.activeConvId}
      onNewChat={chat.createNewChat}
      onSelectConv={chat.selectConversation}
      onRenameConv={chat.renameConversation}
      onTogglePinConv={chat.togglePinConversation}
      onClearConv={chat.removeConversation}
    >
      <Chat chat={chat} />
    </Layout>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth" element={<Auth />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <ProtectedApp />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  )
}

export default App
