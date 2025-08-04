import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Heart, 
  MessageCircle,
  User,
  FileText,
  PieChart,
  MapPin,
  Euro,
  Shield,
  Menu,
  X
} from 'lucide-react'
import { ChatInterface } from './components/ChatInterface'
import { VisualizationPanel } from './components/VisualizationPanel'
import { DocumentUpload } from './components/DocumentUpload'
import { UserProfile } from './components/UserProfile'
import { useUser, useChat } from './store/appStore'

function App() {
  console.log('App component starting...')
  
  const [activePanel, setActivePanel] = useState<'chat' | 'analysis' | 'profile'>('chat')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  console.log('State initialized...')
  
  let user, chatHistory;
  
  try {
    user = useUser()
    console.log('User hook called:', user)
    
    const chatState = useChat()
    chatHistory = chatState.chatHistory
    console.log('Chat hook called:', chatHistory)
  } catch (error) {
    console.error('Error in hooks:', error)
    return <div className="p-4 text-red-600">Error loading app: {String(error)}</div>
  }

  const NavigationButton = ({ 
    icon: Icon, 
    label, 
    panel, 
    count 
  }: { 
    icon: any, 
    label: string, 
    panel: 'chat' | 'analysis' | 'profile',
    count?: number 
  }) => (
    <button
      onClick={() => setActivePanel(panel)}
      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
        activePanel === panel 
          ? 'bg-primary-100 text-primary-700 shadow-sm' 
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span className="font-medium">{label}</span>
      {count && (
        <span className="bg-primary-600 text-white text-xs px-2 py-1 rounded-full">
          {count}
        </span>
      )}
    </button>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="glass-effect border-b border-white/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="medical-gradient p-2 rounded-xl">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Mediflux V2</h1>
                <p className="text-xs text-gray-600">Navigation Santé IA</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-2">
              <NavigationButton 
                icon={MessageCircle} 
                label="Assistant IA" 
                panel="chat"
                count={chatHistory.length}
              />
              <NavigationButton 
                icon={PieChart} 
                label="Analyses" 
                panel="analysis"
              />
              <NavigationButton 
                icon={User} 
                label="Profil" 
                panel="profile"
              />
            </nav>

            {/* Mobile Menu Button */}
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-gray-100"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-8rem)]">
          
          {/* Chat Panel */}
          <div className={`lg:col-span-2 ${activePanel === 'chat' ? 'block' : 'hidden lg:block'}`}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="h-full"
            >
              <ChatInterface />
            </motion.div>
          </div>

          {/* Right Panel */}
          <div className="space-y-6">
            {/* Context Card */}
            {user.profile && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="glass-effect rounded-xl p-4"
              >
                <h3 className="font-semibold text-gray-900 mb-2 flex items-center">
                  <Shield className="w-4 h-4 mr-2 text-primary-600" />
                  Contexte Patient
                </h3>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Mutuelle:</span>
                    <span className="font-medium">{user.profile.mutuelle_type}</span>
                  </div>
                  {user.profile.pathology && (
                    <div className="flex justify-between">
                      <span>Pathologie:</span>
                      <span className="font-medium">{user.profile.pathology}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span>Préférence:</span>
                    <span className="font-medium">{user.profile.preferences}</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Analysis Panel */}
            <AnimatePresence mode="wait">
              {activePanel === 'analysis' && (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="h-full"
                >
                  <VisualizationPanel />
                </motion.div>
              )}

              {activePanel === 'profile' && (
                <motion.div
                  key="profile"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="h-full"
                >
                  <UserProfile />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-effect rounded-xl p-4"
            >
              <h3 className="font-semibold text-gray-900 mb-3">Actions Rapides</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Euro className="w-4 h-4 text-blue-600" />
                  </div>
                  <span className="text-sm font-medium">Simuler remboursement</span>
                </button>
                <button className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <MapPin className="w-4 h-4 text-green-600" />
                  </div>
                  <span className="text-sm font-medium">Optimiser parcours</span>
                </button>
                <button className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-4 h-4 text-purple-600" />
                  </div>
                  <span className="text-sm font-medium">Analyser document</span>
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 md:hidden"
          >
            <div className="absolute inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              className="absolute left-0 top-0 h-full w-64 glass-effect p-6 space-y-4"
            >
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-lg font-semibold">Navigation</h2>
                <button onClick={() => setSidebarOpen(false)}>
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <nav className="space-y-2">
                <div onClick={() => { setActivePanel('chat'); setSidebarOpen(false); }}>
                  <NavigationButton 
                    icon={MessageCircle} 
                    label="Assistant IA" 
                    panel="chat"
                    count={chatHistory.length}
                  />
                </div>
                <div onClick={() => { setActivePanel('analysis'); setSidebarOpen(false); }}>
                  <NavigationButton 
                    icon={PieChart} 
                    label="Analyses" 
                    panel="analysis"
                  />
                </div>
                <div onClick={() => { setActivePanel('profile'); setSidebarOpen(false); }}>
                  <NavigationButton 
                    icon={User} 
                    label="Profil" 
                    panel="profile"
                  />
                </div>
              </nav>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
