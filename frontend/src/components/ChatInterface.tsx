import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Paperclip, Loader, Bot, User } from 'lucide-react'
import { useAppStore, useActions, useChat } from '../store/appStore'
import { DocumentUpload } from './DocumentUpload'

export function ChatInterface() {
  const [message, setMessage] = useState('')
  const [showUpload, setShowUpload] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { chatHistory, isTyping } = useChat()
  const { addChatMessage, setTyping } = useActions()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory, isTyping])

  const handleSendMessage = async () => {
    if (!message.trim()) return
    
    // Add user message (this will trigger API call automatically)
    await addChatMessage({
      type: 'user',
      content: message
    })
    
    setMessage('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getSimulatedResponse = (userMessage: string): string => {
    const lowerMessage = userMessage.toLowerCase()
    
    if (lowerMessage.includes('remboursement') || lowerMessage.includes('coût') || lowerMessage.includes('prix')) {
      return "Je peux vous aider à simuler le remboursement de vos médicaments ou consultations. Pouvez-vous me préciser : quel médicament ou quelle consultation vous intéresse ? Avez-vous votre carte de mutuelle à disposition ?"
    }
    
    if (lowerMessage.includes('parcours') || lowerMessage.includes('médecin') || lowerMessage.includes('spécialiste')) {
      return "Pour optimiser votre parcours de soins, j'ai besoin de quelques informations : quelle est votre pathologie ou symptôme ? Quelle est votre région ? Préférez-vous le secteur public ou privé ?"
    }
    
    if (lowerMessage.includes('document') || lowerMessage.includes('analyser') || lowerMessage.includes('carte')) {
      return "Je peux analyser vos documents médicaux (carte de mutuelle, feuilles de soins, ordonnances). Utilisez le bouton de téléchargement pour m'envoyer votre document, et je vous expliquerai votre couverture."
    }
    
    return "Je comprends votre demande. Pour vous aider au mieux, pouvez-vous me préciser si vous souhaitez : 1) Simuler un remboursement, 2) Optimiser un parcours de soins, ou 3) Analyser un document médical ?"
  }

  return (
    <div className="glass-effect rounded-xl h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-green-500 rounded-full flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Assistant IA Mediflux</h3>
            <p className="text-sm text-gray-600">Simuler • Optimiser • Analyser</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {chatHistory.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start space-x-3 max-w-xs lg:max-w-md ${
                msg.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.type === 'user' 
                    ? 'bg-primary-600' 
                    : 'bg-gradient-to-br from-blue-500 to-green-500'
                }`}>
                  {msg.type === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>
                <div className={`px-4 py-3 rounded-2xl ${
                  msg.type === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  {/* Check if content contains HTML tags */}
                  {msg.content.includes('<') && msg.content.includes('>') ? (
                    <div 
                      className="text-sm"
                      dangerouslySetInnerHTML={{ __html: msg.content }}
                    />
                  ) : (
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  )}
                  <p className={`text-xs mt-1 ${
                    msg.type === 'user' ? 'text-primary-100' : 'text-gray-400'
                  }`}>
                    {msg.timestamp.toLocaleTimeString('fr-FR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-green-500 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Document Upload Modal */}
      <AnimatePresence>
        {showUpload && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 flex items-center justify-center p-4 z-10"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl p-6 max-w-md w-full"
            >
              <DocumentUpload onClose={() => setShowUpload(false)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <div className="relative">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question sur les remboursements, parcours de soins..."
                className="w-full resize-none rounded-lg border border-gray-300 px-4 py-3 pr-12 focus:ring-2 focus:ring-primary-500 focus:border-transparent max-h-32"
                rows={1}
                style={{ minHeight: '44px' }}
              />
              <button
                onClick={() => setShowUpload(true)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <Paperclip className="w-4 h-4" />
              </button>
            </div>
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!message.trim() || isTyping}
            className="btn-primary p-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isTyping ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2 mt-3">
          <button 
            onClick={() => setMessage('Simuler le remboursement de mes médicaments')}
            className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors"
          >
            💊 Remboursement médicaments
          </button>
          <button 
            onClick={() => setMessage('Optimiser mon parcours de soins')}
            className="text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full hover:bg-green-200 transition-colors"
          >
            🏥 Parcours de soins
          </button>
          <button 
            onClick={() => setShowUpload(true)}
            className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded-full hover:bg-purple-200 transition-colors"
          >
            📄 Analyser document
          </button>
        </div>
      </div>
    </div>
  )
}
