import { createContext, useContext, useState } from 'react'
import { login as apiLogin, register as apiRegister } from '../api/client'

const AuthContext = createContext(undefined)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(
    localStorage.getItem('token')
  )

  const handleLogin = async (email, password) => {
    const response = await apiLogin(email, password)
    setToken(response.token)
    localStorage.setItem('token', response.token)
    if (response.refresh) localStorage.setItem('refresh', response.refresh)
  }

  const handleRegister = async (name, email, password) => {
    const response = await apiRegister(name, email, password)
    setToken(response.token)
    localStorage.setItem('token', response.token)
    if (response.refresh) localStorage.setItem('refresh', response.refresh)
  }

  const handleLogout = () => {
    setToken(null)
    localStorage.removeItem('token')
    localStorage.removeItem('refresh')
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

