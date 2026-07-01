import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCollections } from '../store/useCollections.jsx'
import { listDocuments, deleteDocument } from '../api/client'
import { FileText, Trash2, Calendar, FileCheck, AlertCircle } from 'lucide-react'

export default function Documents() {
  const { selectedCollection } = useCollections()
  const [documents, setDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadDocuments = async () => {
    if (!selectedCollection) {
      setDocuments([])
      return
    }

    setIsLoading(true)
    setError(null)
    try {
      const docs = await listDocuments(selectedCollection.id)
      // Ensure docs is always an array
      setDocuments(Array.isArray(docs) ? docs : [])
    } catch (err) {
      setError('Failed to load documents')
      setDocuments([]) // Reset to empty array on error
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCollection])

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      await deleteDocument(docId)
      setDocuments((prev) => prev.filter((d) => d.id !== docId))
    } catch (err) {
      alert('Failed to delete document')
      console.error(err)
    }
  }

  if (!selectedCollection) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center">
          <AlertCircle size={48} className="mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            No Collection Selected
          </h2>
          <p className="text-gray-600 mb-4">
            Please select a collection to view its documents
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Documents</h2>
          <p className="text-gray-600">
            View and manage documents in <span className="font-semibold">{selectedCollection.name}</span>
          </p>
        </div>
        <button
          onClick={loadDocuments}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">Loading documents...</div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {!isLoading && (!Array.isArray(documents) || documents.length === 0) && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <FileText size={64} className="mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              No Documents Yet
            </h3>
            <p className="text-gray-600 mb-4">
              Upload PDF files to get started
            </p>
            <Link
              to="/uploads"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Upload Documents
            </Link>
          </div>
        </div>
      )}

      {!isLoading && Array.isArray(documents) && documents.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <FileText size={24} className="text-blue-600" />
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-1 text-gray-400 hover:text-red-600 rounded"
                  title="Delete document"
                >
                  <Trash2 size={18} />
                </button>
              </div>
              <h3 className="font-semibold text-gray-800 mb-2 truncate" title={doc.name}>
                {doc.name}
              </h3>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <FileCheck size={16} />
                  <span>{doc.pages || 0} pages</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar size={16} />
                  <span>
                    {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                </div>
                {doc.status && (
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        doc.status === 'indexed'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {doc.status}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

