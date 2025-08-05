import { useState } from 'react'
import { motion } from 'framer-motion'
import { User, Shield, MapPin, Heart, Settings, Save, Edit3 } from 'lucide-react'
import { useUser, useActions, type UserProfile as UserProfileType } from '../store/appStore'

export function UserProfile() {
  const { profile } = useUser()
  const { setUserProfile } = useActions()
  const [isEditing, setIsEditing] = useState(!profile)
  const [formData, setFormData] = useState<UserProfileType>(profile || {
    mutuelle_type: '',
    preferences: 'low-cost public',
    pathology: '',
    region: '',
    age_range: ''
  })

  const handleSave = () => {
    setUserProfile(formData)
    setIsEditing(false)
  }

  const mutuelles = [
    'MGEN',
    'MAIF',
    'AXA',
    'Harmonie Mutuelle',
    'MAAF',
    'Groupe VYV',
    'Malakoff Humanis',
    'AG2R La Mondiale',
    'Autre'
  ]

  const regions = [
    'Île-de-France',
    'Auvergne-Rhône-Alpes',
    'Hauts-de-France',
    'Nouvelle-Aquitaine',
    'Occitanie',
    'Grand Est',
    'Provence-Alpes-Côte d\'Azur',
    'Bretagne',
    'Pays de la Loire',
    'Normandie',
    'Bourgogne-Franche-Comté',
    'Centre-Val de Loire',
    'Corse'
  ]

  return (
    <div className="space-y-6">
      <div className="glass-effect rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <User className="w-5 h-5 mr-2 text-primary-600" />
            Profil Patient
          </h3>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <Edit3 className="w-4 h-4" />
          </button>
        </div>

        {isEditing ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {/* Mutuelle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mutuelle / Complémentaire santé
              </label>
              <select
                value={formData.mutuelle_type}
                onChange={(e) => setFormData({ ...formData, mutuelle_type: e.target.value })}
                className="input-field"
              >
                <option value="">Sélectionnez votre mutuelle</option>
                {mutuelles.map(mutuelle => (
                  <option key={mutuelle} value={mutuelle}>{mutuelle}</option>
                ))}
              </select>
            </div>

            {/* Region */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Région
              </label>
              <select
                value={formData.region || ''}
                onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                className="input-field"
              >
                <option value="">Sélectionnez votre région</option>
                {regions.map(region => (
                  <option key={region} value={region}>{region}</option>
                ))}
              </select>
            </div>

            {/* Age Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tranche d'âge
              </label>
              <select
                value={formData.age_range || ''}
                onChange={(e) => setFormData({ ...formData, age_range: e.target.value })}
                className="input-field"
              >
                <option value="">Sélectionnez votre âge</option>
                <option value="18-25">18-25 ans</option>
                <option value="26-35">26-35 ans</option>
                <option value="36-45">36-45 ans</option>
                <option value="46-55">46-55 ans</option>
                <option value="56-65">56-65 ans</option>
                <option value="65+">65+ ans</option>
              </select>
            </div>

            {/* Pathology */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pathologie chronique (optionnel)
              </label>
              <input
                type="text"
                value={formData.pathology || ''}
                onChange={(e) => setFormData({ ...formData, pathology: e.target.value })}
                placeholder="ex: diabète, hypertension, mal de dos chronique..."
                className="input-field"
              />
            </div>

            {/* Preferences */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Préférences de soins
              </label>
              <div className="space-y-2">
                {[
                  { value: 'low-cost public', label: 'Public / Coût minimal' },
                  { value: 'balanced', label: 'Équilibré public/privé' },
                  { value: 'private comfort', label: 'Privé / Confort' },
                  { value: 'speed priority', label: 'Rapidité prioritaire' }
                ].map(option => (
                  <label key={option.value} className="flex items-center">
                    <input
                      type="radio"
                      name="preferences"
                      value={option.value}
                      checked={formData.preferences === option.value}
                      onChange={(e) => setFormData({ ...formData, preferences: e.target.value })}
                      className="mr-3 text-primary-600"
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex space-x-3 pt-4">
              <button
                onClick={() => setIsEditing(false)}
                className="flex-1 btn-secondary"
              >
                Annuler
              </button>
              <button
                onClick={handleSave}
                className="flex-1 btn-primary flex items-center justify-center space-x-2"
              >
                <Save className="w-4 h-4" />
                <span>Sauvegarder</span>
              </button>
            </div>
          </motion.div>
        ) : profile ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="grid grid-cols-1 gap-4">
              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <Shield className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-900">Mutuelle</p>
                  <p className="text-xs text-blue-700">{profile.mutuelle_type}</p>
                </div>
              </div>

              {profile.region && (
                <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                  <MapPin className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium text-green-900">Région</p>
                    <p className="text-xs text-green-700">{profile.region}</p>
                  </div>
                </div>
              )}

              {profile.pathology && (
                <div className="flex items-center space-x-3 p-3 bg-red-50 rounded-lg">
                  <Heart className="w-5 h-5 text-red-600" />
                  <div>
                    <p className="text-sm font-medium text-red-900">Pathologie</p>
                    <p className="text-xs text-red-700">{profile.pathology}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
                <Settings className="w-5 h-5 text-purple-600" />
                <div>
                  <p className="text-sm font-medium text-purple-900">Préférences</p>
                  <p className="text-xs text-purple-700">
                    {profile.preferences === 'low-cost public' && 'Public / Coût minimal'}
                    {profile.preferences === 'balanced' && 'Équilibré public/privé'}
                    {profile.preferences === 'private comfort' && 'Privé / Confort'}
                    {profile.preferences === 'speed priority' && 'Rapidité prioritaire'}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <div className="text-center py-8">
            <User className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-gray-900 mb-1">
              Complétez votre profil
            </h4>
            <p className="text-xs text-gray-600 mb-4">
              Pour des recommandations personnalisées
            </p>
            <button
              onClick={() => setIsEditing(true)}
              className="btn-primary text-sm"
            >
              Créer mon profil
            </button>
          </div>
        )}
      </div>

      {/* Privacy Notice */}
      <div className="glass-effect rounded-xl p-4">
        <div className="flex items-start space-x-3">
          <Shield className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-gray-900">Confidentialité</h4>
            <p className="text-xs text-gray-600 mt-1">
              Vos données sont stockées localement et utilisées uniquement pour personnaliser vos recommandations. 
              Vous pouvez les supprimer à tout moment.
            </p>
            <button className="text-xs text-primary-600 hover:text-primary-700 mt-2">
              Gérer mes données →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
