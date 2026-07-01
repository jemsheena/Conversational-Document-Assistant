import { useState, useEffect } from 'react'
import { Settings as SettingsIcon } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    k: 12,
    rerank_k: 6,
    model: 'gpt-4o-mini',
    max_tokens: 600,
    embed_model: 'sentence-transformers/all-MiniLM-L6-v2',
  })

  useEffect(() => {
    // Load saved settings from localStorage
    const saved = localStorage.getItem('chatSettings')
    if (saved) {
      setSettings(JSON.parse(saved))
    }
  }, [])

  const handleSave = () => {
    localStorage.setItem('chatSettings', JSON.stringify(settings))
    alert('Settings saved!')
  }

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="h-full p-6">
      <div className="max-w-2xl">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <SettingsIcon size={24} className="text-gray-700" />
            <h2 className="text-2xl font-bold text-gray-800">Settings</h2>
          </div>
          <p className="text-gray-600">
            Configure RAG parameters and model preferences
          </p>
        </div>

        <div className="space-y-6">
          {/* Retrieval settings */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Retrieval Settings
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Top-K (initial retrieval)
                </label>
                <input
                  type="number"
                  value={settings.k}
                  onChange={(e) => handleChange('k', parseInt(e.target.value))}
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Number of chunks to retrieve before re-ranking (default: 12)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Re-rank K (final selection)
                </label>
                <input
                  type="number"
                  value={settings.rerank_k}
                  onChange={(e) => handleChange('rerank_k', parseInt(e.target.value))}
                  min="1"
                  max={settings.k}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Number of chunks after re-ranking (default: 6)
                </p>
              </div>
            </div>
          </div>

          {/* Model settings */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Model Settings
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  LLM Model
                </label>
                <select
                  value={settings.model}
                  onChange={(e) => handleChange('model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Tokens
                </label>
                <input
                  type="number"
                  value={settings.max_tokens}
                  onChange={(e) => handleChange('max_tokens', parseInt(e.target.value))}
                  min="100"
                  max="2000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Maximum tokens in the generated response (default: 600)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Embedding Model
                </label>
                <select
                  value={settings.embed_model}
                  onChange={(e) => handleChange('embed_model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="sentence-transformers/all-MiniLM-L6-v2">
                    MiniLM-L6-v2 (local, free)
                  </option>
                  <option value="text-embedding-3-small">
                    OpenAI text-embedding-3-small (API)
                  </option>
                </select>
              </div>
            </div>
          </div>

          {/* Save button */}
          <button
            onClick={handleSave}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}

