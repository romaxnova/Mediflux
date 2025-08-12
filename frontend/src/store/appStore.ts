import { create } from 'zustand'

// API base URL - use environment variable or fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// API helper functions
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`)
  }
  
  return response.json()
}

// Types for the healthcare platform
export interface UserProfile {
  mutuelle_type: string
  pathology?: string
  preferences: string
  region?: string
  age_range?: string
}

export interface ChatMessage {
  id: string
  type: 'user' | 'ai' | 'system'
  content: string
  timestamp: Date
  attachments?: File[]
}

export interface ReimbursementAnalysis {
  id: string
  medication_name?: string
  total_cost: number
  reimbursed_amount: number
  out_of_pocket: number
  coverage_percentage: number
  alternatives?: Array<{
    name: string
    cost: number
    savings: number
  }>
}

export interface CarePathway {
  id: string
  condition: string
  steps: Array<{
    order: number
    provider_type: string
    estimated_cost: number
    wait_time: string
    location?: string
  }>
  total_estimated_cost: number
  estimated_duration: string
}

export interface DocumentAnalysis {
  id: string
  document_type: string
  extracted_data: Record<string, any>
  coverage_info?: {
    dental: number
    optical: number
    consultation: number
  }
  insights: string[]
}

interface AppState {
  // User state
  user: {
    profile: UserProfile | null
    session_id: string
  }
  
  // Chat state
  chatHistory: ChatMessage[]
  isTyping: boolean
  
  // Analysis state
  currentAnalysis: {
    reimbursement?: ReimbursementAnalysis
    pathway?: CarePathway
    document?: DocumentAnalysis
  }
  
  // UI state
  uploadedFiles: File[]
  activeJourney: 'reimbursement' | 'pathway' | 'document' | null
  
  // Actions
  actions: {
    setUserProfile: (profile: UserProfile) => void
    addChatMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
    setTyping: (isTyping: boolean) => void
    setReimbursementAnalysis: (analysis: ReimbursementAnalysis) => void
    setCarePathway: (pathway: CarePathway) => void
    setDocumentAnalysis: (analysis: DocumentAnalysis) => void
    addUploadedFile: (file: File) => void
    removeUploadedFile: (fileName: string) => void
    setActiveJourney: (journey: 'reimbursement' | 'pathway' | 'document' | null) => void
    clearAnalysis: () => void
  }
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  user: {
    profile: null,
    session_id: Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
  },
  
  chatHistory: [
    {
      id: 'welcome',
      type: 'ai',
      content: 'Bonjour ! Je suis votre assistant IA Mediflux. Je peux vous aider à simuler vos remboursements, optimiser vos parcours de soins, et analyser vos documents médicaux. Comment puis-je vous aider aujourd\'hui ?',
      timestamp: new Date()
    }
  ],
  
  isTyping: false,
  
  currentAnalysis: {},
  
  uploadedFiles: [],
  
  activeJourney: null,
  
  // Actions
  actions: {
    setUserProfile: async (profile) => {
      try {
        // Save to backend
        await apiCall('/profile/save', {
          method: 'POST',
          body: JSON.stringify({
            ...profile,
            user_id: get().user.session_id
          })
        })
        
        // Update local state
        set((state) => ({
          user: { ...state.user, profile }
        }))
        
        console.log('Profile saved successfully')
      } catch (error) {
        console.error('Error saving profile:', error)
        // Still update local state even if backend fails
        set((state) => ({
          user: { ...state.user, profile }
        }))
      }
    },
    
    addChatMessage: async (message) => {
      // Add user message immediately
      set((state) => ({
        chatHistory: [
          ...state.chatHistory,
          {
            ...message,
            id: Math.random().toString(36).substring(2, 15),
            timestamp: new Date()
          }
        ]
      }))

      // If it's a user message, send to API and get AI response
      if (message.type === 'user') {
        try {
          set({ isTyping: true })
          
          const response = await apiCall('/chat', {
            method: 'POST',
            body: JSON.stringify({
              message: message.content,
              user_id: get().user.session_id
            })
          })
          
          // Add AI response
          set((state) => ({
            chatHistory: [
              ...state.chatHistory,
              {
                id: Math.random().toString(36).substring(2, 15),
                type: 'ai' as const,
                content: response.response,
                timestamp: new Date()
              }
            ],
            isTyping: false
          }))
          
          // Update analysis data if provided
          if (response.data) {
            const currentAnalysis = get().currentAnalysis
            set({
              currentAnalysis: {
                ...currentAnalysis,
                [response.intent]: response.data
              }
            })
          }
          
        } catch (error) {
          console.error('Error sending message:', error)
          set((state) => ({
            chatHistory: [
              ...state.chatHistory,
              {
                id: Math.random().toString(36).substring(2, 15),
                type: 'ai' as const,
                content: 'Désolé, je ne peux pas traiter votre demande pour le moment. Veuillez réessayer.',
                timestamp: new Date()
              }
            ],
            isTyping: false
          }))
        }
      }
    },
    
    setTyping: (isTyping) => set({ isTyping }),
    
    setReimbursementAnalysis: (analysis) => set((state) => ({
      currentAnalysis: { ...state.currentAnalysis, reimbursement: analysis }
    })),
    
    setCarePathway: (pathway) => set((state) => ({
      currentAnalysis: { ...state.currentAnalysis, pathway }
    })),
    
    setDocumentAnalysis: (analysis) => set((state) => ({
      currentAnalysis: { ...state.currentAnalysis, document: analysis }
    })),
    
    addUploadedFile: (file) => set((state) => ({
      uploadedFiles: [...state.uploadedFiles, file]
    })),
    
    removeUploadedFile: (fileName) => set((state) => ({
      uploadedFiles: state.uploadedFiles.filter(f => f.name !== fileName)
    })),
    
    setActiveJourney: (journey) => set({ activeJourney: journey }),
    
    clearAnalysis: () => set({ currentAnalysis: {} })
  }
}))

// Convenience hooks
export const useUser = () => useAppStore(state => state.user)
export const useChat = () => {
  const chatHistory = useAppStore(state => state.chatHistory)
  const isTyping = useAppStore(state => state.isTyping)
  return { chatHistory, isTyping }
}
export const useAnalysis = () => useAppStore(state => state.currentAnalysis)
export const useActions = () => useAppStore(state => state.actions)
