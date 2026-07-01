import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useCollections } from '../store/useCollections.jsx'
import { ingestDocuments } from '../api/client'
import { Upload, FileText, X } from 'lucide-react'

export default function Uploads() {
  const { selectedCollection, collections, setSelectedCollection } = useCollections()
  const [files, setFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.endsWith('.pdf')
    )
    setFiles((prev) => [...prev, ...droppedFiles])
  }, [])

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files || []).filter((f) =>
      f.name.endsWith('.pdf')
    )
    setFiles((prev) => [...prev, ...selectedFiles])
  }

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (!selectedCollection || files.length === 0) {
      alert('Please select a collection and add PDF files')
      return
    }

    setIsUploading(true)
    setProgress(0)
    setResult(null)

    try {
      const response = await ingestDocuments(selectedCollection.id, files)
      setResult(response)
      setFiles([])
      setProgress(100)
    } catch (error) {
      alert(`Upload failed: ${error.message}`)
    } finally {
      setIsUploading(false)
    }
  }

  if (collections.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <Upload size={64} className="mx-auto mb-4 text-gray-300" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            No Collections Found
          </h2>
          <p className="text-gray-600 mb-6">
            You need to create a collection before you can upload documents
          </p>
          <Link
            to="/collections"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Create Collection
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Upload Documents</h2>
        <p className="text-gray-600">
          Upload PDF files to add them to your collection
        </p>
      </div>

      {/* Collection selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Collection
        </label>
        <div className="flex items-center gap-3">
          <select
            value={selectedCollection?.id || ''}
            onChange={(e) => {
              const coll = collections.find((c) => c.id === e.target.value)
              if (coll) {
                setSelectedCollection(coll)
              }
            }}
            className="flex-1 max-w-md px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {collections.map((coll) => (
              <option key={coll.id} value={coll.id}>
                {coll.name}
              </option>
            ))}
          </select>
          {selectedCollection && (
            <Link
              to="/documents"
              className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 border border-blue-300 rounded-lg hover:bg-blue-50"
            >
              View Documents
            </Link>
          )}
        </div>
        {!selectedCollection && (
          <p className="mt-2 text-sm text-amber-600">
            ⚠️ Please select a collection to upload files
          </p>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className={`flex-1 border-2 border-dashed rounded-lg p-8 text-center ${
          files.length > 0
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 bg-gray-50'
        }`}
      >
        <input
          type="file"
          id="file-input"
          className="hidden"
          multiple
          accept=".pdf"
          onChange={handleFileInput}
        />
        <label
          htmlFor="file-input"
          className="cursor-pointer flex flex-col items-center justify-center h-full"
        >
          <Upload size={48} className="text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-700 mb-2">
            Drag and drop PDF files here
          </p>
          <p className="text-sm text-gray-500 mb-4">or click to browse</p>
          <button
            type="button"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Select Files
          </button>
        </label>
      </div>

      {/* Files list */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <h3 className="font-medium text-gray-700">Selected files:</h3>
          {files.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg"
            >
              <FileText size={20} className="text-blue-600" />
              <span className="flex-1 text-sm text-gray-700">{file.name}</span>
              <span className="text-xs text-gray-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
              <button
                onClick={() => removeFile(idx)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload button */}
      {files.length > 0 && (
        <div className="mt-4 space-y-3">
          <button
            onClick={handleUpload}
            disabled={isUploading || !selectedCollection}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isUploading ? `Uploading... ${progress}%` : 'Upload & Index'}
          </button>
          {!selectedCollection && (
            <p className="text-sm text-amber-600 text-center">
              ⚠️ Please select a collection above to upload files
            </p>
          )}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800 mb-2">
            ✅ Successfully indexed {result.indexed} chunks from {result.doc_ids.length}{' '}
            document(s)
          </p>
          <div className="flex gap-3 mt-3">
            <Link
              to="/documents"
              className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              View Documents
            </Link>
            <Link
              to="/"
              className="px-4 py-2 text-sm border border-green-600 text-green-700 rounded-lg hover:bg-green-50"
            >
              Start Chatting
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
