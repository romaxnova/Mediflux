import React from 'react'
import { motion } from 'framer-motion'
import { Badge, CheckCircle, Clock, Euro, FileText, Star, Award, Shield, Activity, TrendingUp, Users, Target } from 'lucide-react'

interface EvidenceMetadata {
  level?: string
  source?: string
  confidence?: number
  last_updated?: string
}

interface MedicationOption {
  name: string
  cost: number
  reimbursement: number
  advantages?: string[]
  dosage?: string
}

interface PathwayStep {
  step: number
  type: string
  timing: string
  rationale: string
  cost?: number
  wait_time?: string
}

interface KnowledgeBasedResponseProps {
  content: string
  evidence?: EvidenceMetadata
  medications?: MedicationOption[]
  pathway_steps?: PathwayStep[]
  quality_indicators?: {
    // Universal indicators
    success_rate?: number
    resolution_time_days?: number
    patient_satisfaction?: number
    // Specific to infection urinaire
    delai_diagnostic?: string
    efficacite_traitement?: number
    cout_moyen?: number
    // Flexible for future pathologies
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
  // Intelligent condition extraction metadata
  condition_extraction?: {
    original_query?: string
    extracted_condition?: string
    confidence?: number
    synonyms?: string[]
  }
  // Cost breakdown information
  cost_breakdown?: {
    total_estimated_cost?: number
    patient_cost?: number
    evidence_based?: boolean
    [key: string]: any
  }
  // Regional context
  regional_context?: {
    location?: string
    data_source?: string
    last_updated?: string
    [key: string]: any
  }
}

const EvidenceBadge: React.FC<{ evidence: EvidenceMetadata }> = ({ evidence }) => {
  const getEvidenceConfig = (level?: string) => {
    switch (level?.toUpperCase()) {
      case 'A': return {
        color: 'from-emerald-500 to-green-600',
        bg: 'bg-emerald-50',
        text: 'text-emerald-800',
        border: 'border-emerald-200',
        label: 'Preuve solide'
      }
      case 'B': return {
        color: 'from-blue-500 to-indigo-600',
        bg: 'bg-blue-50',
        text: 'text-blue-800',
        border: 'border-blue-200',
        label: 'Preuve modérée'
      }
      case 'C': return {
        color: 'from-amber-500 to-orange-600',
        bg: 'bg-amber-50',
        text: 'text-amber-800',
        border: 'border-amber-200',
        label: 'Preuve limitée'
      }
      default: return {
        color: 'from-gray-500 to-slate-600',
        bg: 'bg-gray-50',
        text: 'text-gray-800',
        border: 'border-gray-200',
        label: 'Analyse générale'
      }
    }
  }

  const config = getEvidenceConfig(evidence.level)

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center gap-3 mb-4"
    >
      <div className={`flex items-center gap-2 px-3 py-2 rounded-xl ${config.bg} ${config.border} border-2 shadow-sm`}>
        <div className={`w-3 h-3 rounded-full bg-gradient-to-br ${config.color} shadow-sm`}></div>
        <span className={`font-semibold text-sm ${config.text}`}>
          Niveau {evidence.level || '?'} - {config.label}
        </span>
      </div>
      {evidence.confidence && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-violet-50 to-purple-50 border-2 border-violet-200 shadow-sm">
          <Activity className="w-4 h-4 text-violet-600" />
          <span className="font-semibold text-sm text-violet-800">
            {Math.round(evidence.confidence * 100)}% fiabilité
          </span>
        </div>
      )}
    </motion.div>
  )
}

const MedicationCard: React.FC<{ medication: MedicationOption; index: number }> = ({ medication, index }) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.1 }}
    className="group bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300"
  >
    <div className="flex justify-between items-start mb-3">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"></div>
        <h4 className="font-semibold text-gray-900">{medication.name}</h4>
      </div>
      <div className="flex items-center gap-1 px-2 py-1 bg-green-100 rounded-lg border border-green-200">
        <Euro className="w-3 h-3 text-green-700" />
        <span className="text-sm font-bold text-green-800">{medication.cost.toFixed(2)}€</span>
      </div>
    </div>
    
    {medication.dosage && (
      <div className="mb-3 p-2 bg-white/60 rounded-lg border border-blue-100">
        <p className="text-xs font-medium text-gray-700">📋 {medication.dosage}</p>
      </div>
    )}
    
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-1 px-3 py-1 bg-gradient-to-r from-emerald-100 to-green-100 rounded-full border border-emerald-200">
        <CheckCircle className="w-3 h-3 text-emerald-600" />
        <span className="text-xs font-semibold text-emerald-700">
          {Math.round(medication.reimbursement * 100)}% remboursé
        </span>
      </div>
      {medication.advantages && medication.advantages.length > 0 && (
        <span className="text-xs text-gray-600 italic max-w-24 truncate">
          {medication.advantages[0]}
        </span>
      )}
    </div>
  </motion.div>
)

const PathwayStepCard: React.FC<{ step: PathwayStep; index: number }> = ({ step, index }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.15 }}
    className="group bg-white border-2 border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-lg hover:border-blue-300 transition-all duration-300"
  >
    <div className="flex items-start gap-4">
      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-md flex-shrink-0">
        {step.step}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-gray-900 text-sm mb-2 group-hover:text-blue-700 transition-colors">
          {step.type}
        </h4>
        {step.rationale && (
          <div className="mb-3 p-2 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-xs text-gray-700 leading-relaxed">{step.rationale}</p>
          </div>
        )}
        <div className="flex items-center gap-4 text-xs">
          {step.timing && (
            <div className="flex items-center gap-1 px-2 py-1 bg-orange-50 rounded-lg border border-orange-200">
              <Clock className="w-3 h-3 text-orange-600" />
              <span className="font-medium text-orange-700">{step.timing}</span>
            </div>
          )}
          {step.cost && (
            <div className="flex items-center gap-1 px-2 py-1 bg-green-50 rounded-lg border border-green-200">
              <Euro className="w-3 h-3 text-green-600" />
              <span className="font-medium text-green-700">{step.cost.toFixed(2)}€</span>
            </div>
          )}
        </div>
      </div>
    </div>
  </motion.div>
)

const QualityIndicators: React.FC<{ indicators: NonNullable<KnowledgeBasedResponseProps['quality_indicators']> }> = ({ indicators }) => {
  // Define which indicators to display and their formatting
  const indicatorConfigs = [
    {
      key: 'efficacite_traitement',
      icon: Target,
      label: 'Efficacité',
      format: (value: any) => `${Math.round(value * 100)}%`,
      condition: (value: any) => typeof value === 'number'
    },
    {
      key: 'delai_diagnostic',
      icon: Clock,
      label: 'Diagnostic',
      format: (value: any) => value,
      condition: (value: any) => value
    },
    {
      key: 'cout_moyen',
      icon: Euro,
      label: 'Coût moyen',
      format: (value: any) => `${value.toFixed(0)}€`,
      condition: (value: any) => typeof value === 'number'
    },
    {
      key: 'patient_satisfaction',
      icon: Users,
      label: 'Satisfaction',
      format: (value: any) => `${value}/5`,
      condition: (value: any) => typeof value === 'number'
    },
    {
      key: 'success_rate',
      icon: TrendingUp,
      label: 'Réussite',
      format: (value: any) => `${Math.round(value * 100)}%`,
      condition: (value: any) => typeof value === 'number'
    },
    {
      key: 'resolution_time_days',
      icon: Clock,
      label: 'Résolution',
      format: (value: any) => `${value}j`,
      condition: (value: any) => typeof value === 'number'
    }
  ]

  // Filter to only display indicators that exist and meet conditions
  const displayIndicators = indicatorConfigs.filter(config => 
    indicators[config.key] && config.condition(indicators[config.key])
  )

  if (displayIndicators.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 }}
      className="bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 border-2 border-emerald-200 rounded-xl p-4 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="w-4 h-4 text-emerald-600" />
        <h4 className="text-sm font-semibold text-emerald-800">Indicateurs de performance</h4>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        {displayIndicators.map((config, index) => {
          const IconComponent = config.icon
          const value = indicators[config.key]
          return (
            <div key={config.key} className="flex items-center gap-2 p-2 bg-white/60 rounded-lg border border-emerald-100">
              <IconComponent className="w-3 h-3 text-emerald-600" />
              <div>
                <div className="font-bold text-emerald-800">{config.format(value)}</div>
                <div className="text-emerald-600">{config.label}</div>
              </div>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}

const DocumentAnalysisCard: React.FC<{ 
  document_type: string
  extracted_data: Record<string, any>
  coverage_info?: Record<string, any>
  insights?: string[]
  confidence?: number 
}> = ({ document_type, extracted_data, coverage_info, insights, confidence }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.3 }}
    className="bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50 border-2 border-purple-200 rounded-xl p-4 shadow-sm"
  >
    <div className="flex items-center gap-2 mb-3">
      <FileText className="w-4 h-4 text-purple-600" />
      <h4 className="text-sm font-semibold text-purple-800">Analyse de document</h4>
      {confidence && (
        <div className="ml-auto flex items-center gap-1 px-2 py-1 bg-purple-100 rounded-full">
          <CheckCircle className="w-3 h-3 text-purple-600" />
          <span className="text-xs font-medium text-purple-700">{Math.round(confidence * 100)}%</span>
        </div>
      )}
    </div>
    
    <div className="space-y-3">
      {/* Document type */}
      <div className="flex items-center gap-2 p-2 bg-white/60 rounded-lg border border-purple-100">
        <Badge className="w-3 h-3 text-purple-600" />
        <span className="text-sm font-medium text-purple-800">Type: {document_type}</span>
      </div>
      
      {/* Coverage info */}
      {coverage_info && Object.keys(coverage_info).length > 0 && (
        <div className="p-3 bg-white/60 rounded-lg border border-purple-100">
          <h5 className="text-xs font-semibold text-purple-700 mb-2">Couverture détectée</h5>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(coverage_info).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-purple-600 capitalize">{key}:</span>
                <span className="font-medium text-purple-800">{value}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Key insights */}
      {insights && insights.length > 0 && (
        <div className="p-3 bg-white/60 rounded-lg border border-purple-100">
          <h5 className="text-xs font-semibold text-purple-700 mb-2">Points clés</h5>
          <ul className="space-y-1">
            {insights.slice(0, 3).map((insight, index) => (
              <li key={index} className="text-xs text-purple-600 flex items-start gap-1">
                <div className="w-1 h-1 bg-purple-400 rounded-full mt-1.5 flex-shrink-0"></div>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  </motion.div>
)

// Simple markdown processor for content
const processMarkdown = (text: string): JSX.Element => {
  const processedText = text
    // Bold text: **text** -> <strong>text</strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic text: *text* -> <em>text</em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Code: `text` -> <code>text</code>
    .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-xs">$1</code>')

  return (
    <div 
      className="text-sm text-gray-800 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: processedText }}
    />
  )
}

export const KnowledgeBasedResponse: React.FC<KnowledgeBasedResponseProps> = ({
  content,
  evidence,
  medications,
  pathway_steps,
  quality_indicators,
  sources,
  // Document analysis props
  document_type,
  extracted_data,
  coverage_info,
  insights,
  confidence,
  // Intelligent extraction props
  condition_extraction,
  cost_breakdown,
  regional_context
}) => {
  // Check if this is a knowledge-based response
  const isKnowledgeBased = evidence || medications || pathway_steps || quality_indicators || document_type

  // Check if this is a document analysis response
  const isDocumentAnalysis = document_type && (extracted_data || coverage_info || insights)

  if (!isKnowledgeBased) {
    // Fallback to simple content display with markdown processing
    return (
      <div className="text-sm whitespace-pre-wrap text-gray-700 leading-relaxed">
        {processMarkdown(content)}
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-4"
    >
      {/* Evidence badge */}
      {evidence && <EvidenceBadge evidence={evidence} />}
      
      {/* Condition extraction confidence */}
      {condition_extraction && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-3 border border-indigo-200"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                <Shield className="w-3 h-3 text-white" />
              </div>
              <span className="text-sm font-medium text-indigo-800">
                Détection: {condition_extraction.extracted_condition || 'N/A'}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${
                (condition_extraction.confidence || 0) >= 0.9 ? 'bg-green-500' :
                (condition_extraction.confidence || 0) >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <span className="text-xs font-semibold text-indigo-700">
                {Math.round((condition_extraction.confidence || 0) * 100)}%
              </span>
            </div>
          </div>
          {condition_extraction.original_query && (
            <div className="mt-2 text-xs text-indigo-600">
              Query: "{condition_extraction.original_query}"
            </div>
          )}
        </motion.div>
      )}
      
      {/* Main content */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white/50 rounded-lg p-3 border border-gray-100"
      >
        {processMarkdown(content)}
      </motion.div>
      
      {/* Pathway steps */}
      {pathway_steps && pathway_steps.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-3"
        >
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full"></div>
            </div>
            <h4 className="text-sm font-semibold text-gray-800">Parcours recommandé</h4>
          </div>
          <div className="space-y-3 ml-2">
            {pathway_steps.map((step, index) => (
              <PathwayStepCard key={index} step={step} index={index} />
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Medications */}
      {medications && medications.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-3"
        >
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gradient-to-r from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full"></div>
            </div>
            <h4 className="text-sm font-semibold text-gray-800">Traitements médicamenteux</h4>
          </div>
          <div className="space-y-3 ml-2">
            {medications.map((med, index) => (
              <MedicationCard key={index} medication={med} index={index} />
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Quality indicators */}
      {quality_indicators && <QualityIndicators indicators={quality_indicators} />}
      
      {/* Document analysis */}
      {isDocumentAnalysis && (
        <DocumentAnalysisCard
          document_type={document_type!}
          extracted_data={extracted_data || {}}
          coverage_info={coverage_info}
          insights={insights}
          confidence={confidence}
        />
      )}
      
      {/* Sources */}
      {sources && sources.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-r from-slate-50 to-gray-50 border border-slate-200 rounded-xl p-3 shadow-sm"
        >
          <div className="flex items-center gap-2 text-xs">
            <FileText className="w-4 h-4 text-slate-600" />
            <span className="font-semibold text-slate-700">Sources médicales:</span>
            <span className="text-slate-600 font-medium">{sources.join(', ')}</span>
          </div>
        </motion.div>
      )}
      
      {/* Knowledge base indicator */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="flex items-center justify-center gap-3 p-3 bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-200 rounded-xl shadow-sm"
      >
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="absolute inset-0 w-2 h-2 bg-blue-400 rounded-full animate-ping"></div>
          </div>
          <span className="text-xs font-semibold text-blue-800">
            Analyse Mediflux
          </span>
        </div>
        <div className="h-3 w-px bg-blue-300"></div>
        <span className="text-xs text-blue-700 font-medium">
          Base de connaissances médicales certifiée
        </span>
      </motion.div>
    </motion.div>
  )
}
