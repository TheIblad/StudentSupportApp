import { useState } from 'react'
import { supabase } from '../supabaseClient'
import './Login.css'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) alert(error.message)
    setLoading(false)
  }

  const handleSignUp = async (e) => {
    e.preventDefault()
    setLoading(true)
    const { error } = await supabase.auth.signUp({
      email,
      password,
    })

    if (error) {
      alert(error.message)
    } else {
      alert('Check your email for the confirmation link!')
    }
    setLoading(false)
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="app-name">Student Support App</h1>
        <p>Sign in to manage your student life</p>
        <form onSubmit={handleLogin}>
          <input
            className="login-input"
            type="email"
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="login-input"
            type="password"
            placeholder="Your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button className="btn login-btn" disabled={loading}>
            {loading ? 'Loading...' : 'Sign In'}
          </button>
          <button className="btn signup-btn" onClick={handleSignUp} disabled={loading}>
            Sign Up
          </button>
        </form>
      </div>
    </div>
  )
}