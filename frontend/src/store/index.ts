import { create } from 'zustand'
import type {
  UserProfile,
  InsightResponse,
  FitnessPlan,
  ChatMessage,
  CurrentUser,
  Subscription,
} from '../types'

interface AppState {
  // Auth
  currentUser: CurrentUser | null
  subscription: Subscription | null

  // Legacy / profile
  userId: string
  sessionId: string
  user: UserProfile | null
  insights: InsightResponse | null
  fitnessPlan: FitnessPlan | null
  chatMessages: ChatMessage[]
  isLoading: boolean
  error: string | null

  // Auth actions
  setCurrentUser: (user: CurrentUser | null) => void
  setSubscription: (sub: Subscription | null) => void
  logout: () => void

  // Data actions
  setUserId: (id: string) => void
  setUser: (user: UserProfile) => void
  setInsights: (data: InsightResponse) => void
  setFitnessPlan: (plan: FitnessPlan) => void
  addChatMessage: (msg: ChatMessage) => void
  setLoading: (v: boolean) => void
  setError: (msg: string | null) => void
  clearChat: () => void
}

export const useStore = create<AppState>((set) => ({
  currentUser: null,
  subscription: null,

  userId: '',
  sessionId: crypto.randomUUID(),
  user: null,
  insights: null,
  fitnessPlan: null,
  chatMessages: [],
  isLoading: false,
  error: null,

  setCurrentUser: (user) =>
    set({ currentUser: user, userId: user?.sub ?? '' }),
  setSubscription: (sub) => set({ subscription: sub }),
  logout: () => {
    localStorage.removeItem('token')
    set({ currentUser: null, subscription: null, userId: '', user: null })
  },

  setUserId: (id) => set({ userId: id }),
  setUser: (user) => set({ user }),
  setInsights: (data) => set({ insights: data }),
  setFitnessPlan: (plan) => set({ fitnessPlan: plan }),
  addChatMessage: (msg) =>
    set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  setLoading: (v) => set({ isLoading: v }),
  setError: (msg) => set({ error: msg }),
  clearChat: () => set({ chatMessages: [] }),
}))
