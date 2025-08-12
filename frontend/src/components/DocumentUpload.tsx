import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import { useActions } from '../store/appStore'
import { getApiUrl } from '../config/api'

interface DocumentUploadProps {
  onClose: () => void
}

export function DocumentUpload({ onClose }: DocumentUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  
  const { addChatMessage, setActiveJourney } = useActions()

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files))
    }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const handleFiles = (files: File[]) => {
    const validFiles = files.filter(file => {
      const validTypes = ['image/jpeg', 'image/png', 'application/pdf', 'image/jpg']
      const maxSize = 10 * 1024 * 1024 // 10MB
      return validTypes.includes(file.type) && file.size <= maxSize
    })
    
    setUploadedFiles(prev => [...prev, ...validFiles])
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return
    
    setUploading(true)
    
    try {
      const file = uploadedFiles[0]
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(getApiUrl('/document/analyze'), {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error('Upload failed')
      }
      
      const result = await response.json()
      
      // Use the formatted HTML analysis from the enhanced analyzer
      let analysisContent = `J'ai analysé votre document "${file.name}".`
      
      if (result.analysis && result.analysis.formatted_analysis) {
        // Use the rich HTML formatted analysis
        analysisContent = result.analysis.formatted_analysis
      } else if (result.analysis && result.analysis.interpretation) {
        // Fallback to the markdown interpretation
        analysisContent = result.analysis.interpretation
      } else if (result.analysis && typeof result.analysis === 'object') {
        // Fallback formatting for other response formats
        const analysis = result.analysis
        
        if (analysis.success) {
          let fallbackText = `📄 **Résultats de l'analyse**\n\n`
          
          if (analysis.document_type) {
            fallbackText += `**Type de document :** ${analysis.document_type}\n`
          }
          
          if (analysis.confidence) {
            fallbackText += `**Niveau de confiance :** ${analysis.confidence}%\n\n`
          }
          
          // Add member info if available
          if (analysis.member_info) {
            const member = analysis.member_info
            fallbackText += '**👤 Informations extraites :**\n'
            if (member.name) fallbackText += `• Nom : ${member.name}\n`
            if (member.adherent_number) fallbackText += `• N° adhérent : ${member.adherent_number}\n`
            if (member.amc_number) fallbackText += `• N° AMC : ${member.amc_number}\n`
            if (member.validity_period) fallbackText += `• Validité : ${member.validity_period}\n`
          }
          
          // Add coverage info if available
          if (analysis.coverage && analysis.coverage.extracted_categories) {
            fallbackText += '\n**💼 Couvertures détectées :**\n'
            analysis.coverage.extracted_categories.forEach((cat: any) => {
              fallbackText += `• ${cat.code}: ${cat.description} - ${cat.percentage}\n`
            })
          }
          
          analysisContent = fallbackText
          
        } else {
          analysisContent += `\n\n❌ L'analyse a échoué : ${analysis.error || 'Erreur inconnue'}`
        }
      } else if (typeof result.analysis === 'string') {
        analysisContent = result.analysis
      }
      
      // Add AI message about the analysis
      addChatMessage({
        type: 'ai',
        content: analysisContent
      })
      
      setActiveJourney('document')
      setUploading(false)
      onClose()
      
    } catch (error) {
      console.error('Upload error:', error)
      setUploading(false)
      
      // Add error message
      addChatMessage({
        type: 'ai',
        content: 'Désolé, je n\'ai pas pu analyser votre document. Veuillez réessayer ou vérifier que le fichier est au bon format.'
      })
    }
  }

  const getDocumentType = (filename: string): string => {
    const name = filename.toLowerCase()
    if (name.includes('carte') || name.includes('mutuelle')) return 'Carte de mutuelle'
    if (name.includes('feuille') || name.includes('soin')) return 'Feuille de soins'
    if (name.includes('ordonnance')) return 'Ordonnance médicale'
    if (name.includes('facture')) return 'Facture médicale'
    return 'Document médical'
  }

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return '📄'
    if (fileType.includes('image')) return '🖼️'
    return '📋'
  }

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Télécharger un document</h3>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-4">
        {/* Upload Area */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="space-y-2">
            <Upload className="w-8 h-8 text-gray-400 mx-auto" />
            <div>
              <p className="text-sm font-medium text-gray-900">
                Glissez vos documents ici ou cliquez pour parcourir
              </p>
              <p className="text-xs text-gray-500 mt-1">
                PDF, JPG, PNG jusqu'à 10MB
              </p>
            </div>
          </div>
        </div>

        {/* File List */}
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-900">Documents sélectionnés:</h4>
            {uploadedFiles.map((file, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{getFileIcon(file.type)}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB • {getDocumentType(file.name)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            ))}
          </div>
        )}

        {/* Supported Documents Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-900">Documents supportés</h4>
              <div className="text-xs text-blue-700 mt-1 space-y-1">
                <p>📋 Carte de mutuelle / tiers payant</p>
                <p>🧾 Feuilles de soins</p>
                <p>💊 Ordonnances médicales</p>
                <p>🏥 Factures d'établissements de santé</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 btn-secondary"
          >
            Annuler
          </button>
          <button
            onClick={handleUpload}
            disabled={uploadedFiles.length === 0 || uploading}
            className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {uploading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Analyse...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                <span>Analyser ({uploadedFiles.length})</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
