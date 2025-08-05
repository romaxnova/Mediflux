import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Euro, TrendingUp, MapPin, Clock, Users } from 'lucide-react'
import { useAnalysis } from '../store/appStore'

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export function VisualizationPanel() {
  const analysis = useAnalysis()

  // Sample data for demonstration
  const reimbursementData = [
    { name: 'Remboursé Sécu', value: 70, color: '#10b981' },
    { name: 'Remboursé Mutuelle', value: 20, color: '#2563eb' },
    { name: 'Reste à charge', value: 10, color: '#ef4444' }
  ]

  const monthlyTrends = [
    { month: 'Jan', depenses: 120, rembourse: 85 },
    { month: 'Fév', depenses: 95, rembourse: 70 },
    { month: 'Mar', depenses: 180, rembourse: 130 },
    { month: 'Avr', depenses: 75, rembourse: 60 },
    { month: 'Mai', depenses: 160, rembourse: 115 }
  ]

  const pathwaySteps = [
    { step: 'Médecin traitant', cost: 25, waitTime: '2-3 jours', location: 'Secteur 1' },
    { step: 'Spécialiste', cost: 50, waitTime: '1-2 semaines', location: 'Secteur 2' },
    { step: 'Examens', cost: 80, waitTime: '3-5 jours', location: 'Public' },
    { step: 'Suivi', cost: 25, waitTime: '1 semaine', location: 'Secteur 1' }
  ]

  return (
    <div className="space-y-6">
      <div className="glass-effect rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <PieChart className="w-5 h-5 mr-2 text-primary-600" />
          Analyses & Visualisations
        </h3>

        {/* Reimbursement Analysis */}
        {analysis.reimbursement ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">Simulation Remboursement</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-700">Coût total:</span>
                  <span className="font-semibold ml-2">{analysis.reimbursement.total_cost}€</span>
                </div>
                <div>
                  <span className="text-blue-700">Reste à charge:</span>
                  <span className="font-semibold ml-2">{analysis.reimbursement.out_of_pocket}€</span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="space-y-6">
            {/* Sample Reimbursement Pie Chart */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Répartition des Remboursements</h4>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={reimbursementData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {reimbursementData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value}%`, 'Pourcentage']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {reimbursementData.map((item, index) => (
                  <div key={index} className="flex items-center text-xs">
                    <div 
                      className="w-3 h-3 rounded-full mr-1" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span>{item.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Monthly Trends */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Évolution Mensuelle</h4>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthlyTrends}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis dataKey="month" className="text-xs" />
                    <YAxis className="text-xs" />
                    <Tooltip formatter={(value) => [`${value}€`, '']} />
                    <Line 
                      type="monotone" 
                      dataKey="depenses" 
                      stroke="#ef4444" 
                      strokeWidth={2}
                      name="Dépenses"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="rembourse" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      name="Remboursé"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Care Pathway Visualization */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Parcours de Soins Recommandé</h4>
              <div className="space-y-3">
                {pathwaySteps.map((step, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border border-blue-100"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-semibold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{step.step}</p>
                        <p className="text-xs text-gray-600">{step.location}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center text-xs text-gray-600 mb-1">
                        <Euro className="w-3 h-3 mr-1" />
                        <span>{step.cost}€</span>
                      </div>
                      <div className="flex items-center text-xs text-gray-600">
                        <Clock className="w-3 h-3 mr-1" />
                        <span>{step.waitTime}</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
              
              <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-green-900">Coût total estimé:</span>
                  <span className="font-semibold text-green-900">
                    {pathwaySteps.reduce((sum, step) => sum + step.cost, 0)}€
                  </span>
                </div>
                <p className="text-xs text-green-700 mt-1">
                  Économie estimée vs parcours privé: 120€
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-effect rounded-xl p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-600">Économies ce mois</p>
              <p className="text-lg font-semibold text-gray-900">156€</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass-effect rounded-xl p-4"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-gray-600">Consultations</p>
              <p className="text-lg font-semibold text-gray-900">8</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
