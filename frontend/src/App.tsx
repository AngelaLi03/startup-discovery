import React, { useState } from 'react'
import { searchStartups, askQuestion } from './api'
import './App.css'

interface Startup {
  id: number
  name: string
  description: string
  industry: string
  funding: string
  location: string
  founded: number
  team_size: number
  similarity_score: number
  rank: number
}

interface QAResponse {
  question: string
  answer: string
}

function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [qaQuery, setQaQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Startup[]>([])
  const [qaResponse, setQaResponse] = useState<QAResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'search' | 'qa'>('search')

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setLoading(true)
    try {
      const results = await searchStartups(searchQuery)
      setSearchResults(results)
    } catch (error) {
      console.error('Search failed:', error)
      alert('Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAsk = async () => {
    if (!qaQuery.trim()) return
    
    setLoading(true)
    try {
      const response = await askQuestion(qaQuery)
      setQaResponse(response)
    } catch (error) {
      console.error('Q&A failed:', error)
      alert('Q&A failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Startup Discovery
          </h1>
          <p className="text-gray-600">
            RAG-powered semantic search and Q&A for startup data
          </p>
        </header>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-white rounded-lg shadow-sm border">
            <button
              onClick={() => setActiveTab('search')}
              className={`px-6 py-3 rounded-l-lg font-medium transition-colors ${
                activeTab === 'search'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              🔍 Search Startups
            </button>
            <button
              onClick={() => setActiveTab('qa')}
              className={`px-6 py-3 rounded-r-lg font-medium transition-colors ${
                activeTab === 'qa'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              💬 Ask Questions
            </button>
          </div>
        </div>

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
              <h2 className="text-2xl font-semibold mb-4">Search Startups</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., AI companies in healthcare, fintech startups in NYC..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="space-y-4">
                {searchResults.map((startup) => (
                  <div key={startup.id} className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-xl font-semibold text-gray-900">
                        {startup.name}
                      </h3>
                      <span className="text-sm text-gray-500">
                        Rank #{startup.rank} (Score: {startup.similarity_score.toFixed(3)})
                      </span>
                    </div>
                    <p className="text-gray-700 mb-3">{startup.description}</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-600">Industry:</span>
                        <p className="text-gray-900">{startup.industry}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Location:</span>
                        <p className="text-gray-900">{startup.location}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Funding:</span>
                        <p className="text-gray-900">{startup.funding}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Team Size:</span>
                        <p className="text-gray-900">{startup.team_size} people</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Q&A Tab */}
        {activeTab === 'qa' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
              <h2 className="text-2xl font-semibold mb-4">Ask Questions</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={qaQuery}
                  onChange={(e) => setQaQuery(e.target.value)}
                  placeholder="e.g., What are the most funded AI startups? Which startups are in healthcare?"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
                />
                <button
                  onClick={handleAsk}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? 'Thinking...' : 'Ask'}
                </button>
              </div>
            </div>

            {/* Q&A Response */}
            {qaResponse && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Question:</h3>
                  <p className="text-gray-700 italic">"{qaResponse.question}"</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Answer:</h3>
                  <p className="text-gray-700 leading-relaxed">{qaResponse.answer}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
