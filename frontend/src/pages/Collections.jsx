import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCollections } from '../store/useCollections.jsx'
import { listDocuments } from '../api/client'
import { FolderOpen, Plus, Check, FileText } from 'lucide-react'

export default function Collections() {
  const {
    collections,
    selectedCollection,
    setSelectedCollection,
    createCollection,
  } = useCollections()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newCollectionName, setNewCollectionName] = useState('')
  const [docCounts, setDocCounts] = useState({})

  useEffect(() => {
    // Load document counts for all collections
    const loadDocCounts = async () => {
      const counts = {}
      for (const coll of collections) {
        try {
          const docs = await listDocuments(coll.id)
          counts[coll.id] = docs.length
        } catch (error) {
          counts[coll.id] = 0
        }
      }
      setDocCounts(counts)
    }
    if (collections.length > 0) {
      loadDocCounts()
    }
  }, [collections])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newCollectionName.trim()) return

    try {
      await createCollection(newCollectionName.trim())
      setNewCollectionName('')
      setShowCreateForm(false)
    } catch (error) {
      alert('Failed to create collection')
    }
  }

  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Collections</h2>
          <p className="text-gray-600">
            Organize your documents into collections
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          New Collection
        </button>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg">
          <form onSubmit={handleCreate} className="flex gap-2">
            <input
              type="text"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              placeholder="Collection name"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(false)
                setNewCollectionName('')
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </form>
        </div>
      )}

      {/* Collections list */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {collections.map((collection) => (
          <div
            key={collection.id}
            onClick={() => setSelectedCollection(collection)}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
              selectedCollection?.id === collection.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <FolderOpen
                size={24}
                className={selectedCollection?.id === collection.id ? 'text-blue-600' : 'text-gray-400'}
              />
              {selectedCollection?.id === collection.id && (
                <Check size={20} className="text-blue-600" />
              )}
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">{collection.name}</h3>
            <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
              <div className="flex items-center gap-1">
                <FileText size={14} />
                <span>{docCounts[collection.id] ?? 0} documents</span>
              </div>
              <span>•</span>
              <span>{new Date(collection.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedCollection(collection)
                }}
                className="flex-1 px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Select
              </button>
              <Link
                to="/documents"
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedCollection(collection)
                }}
                className="flex-1 px-3 py-1.5 text-xs border border-gray-300 text-gray-700 rounded hover:bg-gray-50 text-center"
              >
                View Docs
              </Link>
            </div>
          </div>
        ))}

        {collections.length === 0 && (
          <div className="col-span-full text-center py-12">
            <div className="max-w-md mx-auto">
              <FolderOpen size={64} className="mx-auto mb-4 text-gray-300" />
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                No Collections Yet
              </h3>
              <p className="text-gray-600 mb-6">
                Create your first collection to organize and chat with your documents
              </p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center gap-2 mx-auto"
              >
                <Plus size={20} />
                Create Your First Collection
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

