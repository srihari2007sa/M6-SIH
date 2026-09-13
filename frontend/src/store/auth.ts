import { create } from 'zustand' // will be added if not present; using simple localStorage pattern
import type { User } from '../types'

// Simple auth store using localStorage + module-level state
interface AuthState {
  user: User | null
  token: string | null
  setAuth: (token: string, user: User) => void
  clearAuth: () => void
}

// Minimal zustand-like store using React module state
let _user: User | null = null
let _token: string | null = localStorage.getItem('token')
const _listeners: Set<() => void> = new Set()

function notify() { _listeners.forEach(l => l()) }

export const authStore = {
  getUser: () => _user,
  getToken: () => _token,
  setAuth: (token: string, user: User) => {
    _token = token; _user = user
    localStorage.setItem('token', token)
    notify()
  },
  clearAuth: () => {
    _token = null; _user = null
    localStorage.removeItem('token')
    notify()
  },
  subscribe: (listener: () => void) => {
    _listeners.add(listener)
    return () => _listeners.delete(listener)
  },
}
