import { useState } from 'react'
import { useAuth } from '../store/useAuth.jsx'
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login: authLogin, register: authRegister } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isLogin) {
        await authLogin(email, password)
      } else {
        await authRegister(name, email, password)
      }
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((item) => item.msg).join(', '))
      } else {
        setError(detail || err.message || 'Authentication failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <Sparkles size={24} color="white" />
        </div>
        <h1>{isLogin ? 'Welcome back' : 'Create account'}</h1>
        <p>{isLogin ? 'Log in to your Document Assistant' : 'Sign up for Document Assistant'}</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <input
              className="auth-input"
              type="text"
              placeholder="Full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              required
            />
          )}
          <input
            className="auth-input"
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="auth-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Please wait...' : (isLogin ? 'Log in' : 'Sign up')}
          </button>
        </form>

        <div className="auth-toggle">
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <button onClick={() => { setIsLogin(!isLogin); setError(''); setName('') }}>
            {isLogin ? 'Sign up' : 'Log in'}
          </button>
        </div>
      </div>
    </div>
  )
}
