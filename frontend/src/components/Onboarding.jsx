import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, Upload, MessageSquare, Check, ArrowRight } from 'lucide-react'
import { useCollections } from '../store/useCollections.jsx'

export default function Onboarding({ onComplete }) {
  const navigate = useNavigate()
  const { collections, createCollection } = useCollections()
  const [step, setStep] = useState(1)
  const [collectionName, setCollectionName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const steps = [
    {
      id: 1,
      title: 'Create a Collection',
      description: 'Organize your documents into collections',
      icon: FolderOpen,
      action: 'Create Collection',
    },
    {
      id: 2,
      title: 'Upload Documents',
      description: 'Add PDF files to your collection',
      icon: Upload,
      action: 'Upload Files',
    },
    {
      id: 3,
      title: 'Start Chatting',
      description: 'Ask questions about your documents',
      icon: MessageSquare,
      action: 'Start Chat',
    },
  ]

  const handleCreateCollection = async (e) => {
    e.preventDefault()
    if (!collectionName.trim()) return

    setIsCreating(true)
    try {
      await createCollection(collectionName.trim())
      setStep(2)
      navigate('/uploads')
    } catch (error) {
      alert('Failed to create collection')
    } finally {
      setIsCreating(false)
    }
  }

  const handleSkip = () => {
    if (collections.length > 0) {
      setStep(2)
      navigate('/uploads')
    }
  }

  useEffect(() => {
    if (collections.length > 0 && step === 1) {
      // User already has collections, skip to step 2
      setStep(2)
    }
  }, [collections, step])

  return (
    <div className="h-full flex items-center justify-center p-6 bg-gradient-to-br from-blue-50 to-indigo-50 relative">
      <button
        onClick={() => {
          localStorage.setItem('onboardingShown', 'true')
          onComplete?.()
        }}
        className="absolute top-4 right-4 px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
      >
        Skip
      </button>
      <div className="max-w-4xl w-full">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((s, idx) => {
              const Icon = s.icon
              const isActive = step === s.id
              const isCompleted = step > s.id
              
              return (
                <div key={s.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${
                        isCompleted
                          ? 'bg-green-500 border-green-500 text-white'
                          : isActive
                          ? 'bg-blue-600 border-blue-600 text-white'
                          : 'bg-white border-gray-300 text-gray-400'
                      }`}
                    >
                      {isCompleted ? (
                        <Check size={24} />
                      ) : (
                        <Icon size={24} />
                      )}
                    </div>
                    <div className="mt-2 text-center">
                      <p
                        className={`text-sm font-medium ${
                          isActive ? 'text-blue-600' : 'text-gray-500'
                        }`}
                      >
                        {s.title}
                      </p>
                    </div>
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`h-1 flex-1 mx-2 rounded ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          {step === 1 && (
            <div className="text-center">
              <FolderOpen size={64} className="mx-auto mb-4 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Create Your First Collection
              </h2>
              <p className="text-gray-600 mb-6">
                Collections help you organize your documents. Create one to get started!
              </p>
              <form onSubmit={handleCreateCollection} className="max-w-md mx-auto">
                <input
                  type="text"
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                  placeholder="Enter collection name (e.g., 'Research Papers')"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                  autoFocus
                />
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={!collectionName.trim() || isCreating}
                    className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
                  >
                    {isCreating ? 'Creating...' : 'Create Collection'}
                    <ArrowRight size={20} />
                  </button>
                  {collections.length > 0 && (
                    <button
                      type="button"
                      onClick={handleSkip}
                      className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Use Existing
                    </button>
                  )}
                </div>
              </form>
            </div>
          )}

          {step === 2 && (
            <div className="text-center">
              <Upload size={64} className="mx-auto mb-4 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Upload Your Documents
              </h2>
              <p className="text-gray-600 mb-6">
                Add PDF files to your collection. The system will process and index them for chat.
              </p>
              <button
                onClick={() => navigate('/uploads')}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center gap-2 mx-auto"
              >
                Go to Uploads
                <ArrowRight size={20} />
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="text-center">
              <MessageSquare size={64} className="mx-auto mb-4 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Ready to Chat!
              </h2>
              <p className="text-gray-600 mb-6">
                You're all set! Start asking questions about your documents.
              </p>
              <button
                onClick={() => {
                  navigate('/')
                  onComplete?.()
                }}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center gap-2 mx-auto"
              >
                Start Chatting
                <ArrowRight size={20} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

