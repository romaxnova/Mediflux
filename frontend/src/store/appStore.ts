import { create } from 'zustand'

// API base URL
const API_BASE_URL = 'http://localhost:8000'

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
  // Enhanced data for knowledge-based responses
  structured_data?: {
    evidence?: {
      level?: string
      source?: string
      confidence?: number
      last_updated?: string
    }
    medications?: Array<{
      name: string
      cost: number
      reimbursement: number
      advantages?: string[]
      dosage?: string
    }>
    pathway_steps?: Array<{
      step: number
      type: string
      timing: string
      rationale: string
      cost?: number
      wait_time?: string
    }>
    quality_indicators?: {
      success_rate?: number
      resolution_time_days?: number
      patient_satisfaction?: number
      [key: string]: any
    }
    sources?: string[]
    // Document analysis support
    document_type?: string
    extracted_data?: Record<string, any>
    coverage_info?: {
      dental?: number
      optical?: number
      consultation?: number
      [key: string]: any
    }
    insights?: string[]
    confidence?: number
  }
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
          
          // Parse structured data for enhanced display
          const parseStructuredData = (responseData: any) => {
            const structured: any = {}
            
            // Check if we have a care pathway result with structured data
            if (responseData?.results?.type === 'care_pathway' && responseData?.results?.pathway) {
              const pathway = responseData.results.pathway
              
              // Extract evidence information
              if (pathway.evidence) {
                structured.evidence = pathway.evidence
              }
              
              // Extract medications
              if (pathway.medications && pathway.medications.length > 0) {
                structured.medications = pathway.medications
              }
              
              // Extract pathway steps
              if (pathway.pathway_steps && pathway.pathway_steps.length > 0) {
                structured.pathway_steps = pathway.pathway_steps
              }
              
              // Extract quality indicators (flexible for different pathology types)
              if (pathway.quality_indicators) {
                structured.quality_indicators = pathway.quality_indicators
              }
              
              // Extract intelligent condition extraction metadata
              if (pathway.condition_extraction) {
                structured.condition_extraction = pathway.condition_extraction
              }
              
              // Extract cost breakdown
              if (pathway.cost_breakdown) {
                structured.cost_breakdown = pathway.cost_breakdown
              }
              
              // Extract regional context
              if (pathway.regional_context) {
                structured.regional_context = pathway.regional_context
              }
              
              // Extract sources
              const sources = []
              if (pathway.evidence?.source) {
                sources.push(pathway.evidence.source)
              }
              // Support multiple sources for expanded knowledge base
              if (pathway.sources && Array.isArray(pathway.sources)) {
                sources.push(...pathway.sources)
              }
              if (sources.length > 0) {
                structured.sources = [...new Set(sources)] // Remove duplicates
              }
            }
            
            // Future: Add support for other result types as knowledge base expands
            
            // Document analysis with structured insights
            if (responseData?.results?.type === 'document_analysis' && responseData?.results?.analysis) {
              const analysis = responseData.results.analysis
              
              if (analysis.document_type) {
                structured.document_type = analysis.document_type
              }
              if (analysis.extracted_data) {
                structured.extracted_data = analysis.extracted_data
              }
              if (analysis.coverage_info) {
                structured.coverage_info = analysis.coverage_info
              }
              if (analysis.insights && analysis.insights.length > 0) {
                structured.insights = analysis.insights
              }
              if (analysis.confidence) {
                structured.confidence = analysis.confidence
              }
            }
            
            // Reimbursement simulations with structured breakdowns
            // Medication comparisons with structured alternatives
            
            return Object.keys(structured).length > 0 ? structured : undefined
          }
          
          // Add AI response
          set((state) => ({
            chatHistory: [
              ...state.chatHistory,
              {
                id: Math.random().toString(36).substring(2, 15),
                type: 'ai' as const,
                content: response.response,
                timestamp: new Date(),
                structured_data: parseStructuredData(response.data)
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
