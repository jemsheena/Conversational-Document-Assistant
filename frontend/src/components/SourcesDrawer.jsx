import { X, FileText } from 'lucide-react'

export default function SourcesDrawer({ isOpen, onClose, sources = [] }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">Sources</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Sources list */}
        <div className="flex-1 overflow-y-auto p-4">
          {sources.length === 0 ? (
            <p className="text-gray-500 text-sm">No sources available</p>
          ) : (
            <div className="space-y-4">
              {sources.map((source, idx) => (
                <div
                  key={idx}
                  className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-start gap-2 mb-2">
                    <FileText size={16} className="text-blue-600 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-gray-800 truncate">
                        {source.doc}
                      </p>
                      <p className="text-xs text-gray-500">
                        Page {source.page} • Score: {source.score.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-3">
                    {source.snippet}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}




