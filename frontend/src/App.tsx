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
  similarity_percentage: number
  similarity_label: string
  similarity_color: string
  match_reason: string
  calibration_info: {
    z_score: number
    background_mean: number
    background_std: number
  }
  rank: number
  // Optional fields that might be present
  source?: string
  source_id?: string
  content_hash?: string
  updated_at?: string
  homepage_url?: string
  linkedin_url?: string
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
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="container mx-auto px-4 py-8 w-full">
        {/* Centered Header */}
        <header className="text-center mb-12 w-full">
          <h1 className="text-5xl font-bold text-gray-900 mb-4 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Startup Discovery
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            RAG-powered semantic search and Q&A for startup data
          </p>
        </header>

        {/* Centered Tab Navigation */}
        <div className="flex justify-center mb-10 w-full">
          <div className="flex bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => setActiveTab('search')}
              className={`px-8 py-4 font-semibold transition-all duration-300 ${
                activeTab === 'search'
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg transform scale-105'
                  : 'bg-white text-gray-700 hover:bg-gray-50 hover:text-blue-600'
              }`}
            >
              🔍 Search Startups
            </button>
            <button
              onClick={() => setActiveTab('qa')}
              className={`px-8 py-4 font-semibold transition-all duration-300 ${
                activeTab === 'qa'
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg transform scale-105'
                  : 'bg-white text-gray-700 hover:bg-gray-50 hover:text-blue-600'
              }`}
            >
              💬 Ask Questions
            </button>
          </div>
        </div>

        {/* Centered Content */}
        <div className="content-wrapper">
            {/* Search Tab */}
            {activeTab === 'search' && (
              <div className="space-y-6">
                {/* Search Input */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 text-center">
                  <h2 className="text-3xl font-bold text-gray-900 mb-6">Search Startups</h2>
                  <div className="flex gap-4 max-w-2xl mx-auto">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="e.g., AI companies in healthcare, fintech startups in NYC..."
                      className="flex-1 px-6 py-4 border border-gray-300 rounded-lg focus:ring-4 focus:ring-blue-200 focus:border-blue-500 text-lg transition-all duration-300"
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <button
                      onClick={handleSearch}
                      disabled={loading}
                      className="px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                    >
                      {loading ? '🔍 Searching...' : 'Search'}
                    </button>
                  </div>
                </div>

                {/* Search Results */}
                {searchResults.length > 0 && (
                  <div className="space-y-6">
                    <h3 className="text-2xl font-bold text-gray-900 text-center mb-6">
                      Found {searchResults.length} Results
                    </h3>
                    {searchResults.map((startup, index) => (
                      <div key={startup.id} className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]">
                        <div className="flex justify-between items-start mb-4">
                          <h3 className="text-2xl font-bold text-gray-900">
                            {startup.name}
                          </h3>
                          <div className="text-right">
                            <div className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full mb-2">
                              Rank #{startup.rank}
                            </div>
                            <div className={`text-lg font-bold px-3 py-2 rounded-lg ${
                              startup.similarity_color === '🟢' ? 'bg-green-100 text-green-800' :
                              startup.similarity_color === '🟡' ? 'bg-yellow-100 text-yellow-800' :
                              startup.similarity_color === '🟠' ? 'bg-orange-100 text-orange-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {startup.similarity_color} {startup.similarity_percentage}% - {startup.similarity_label}
                            </div>
                          </div>
                        </div>
                        <p className="text-gray-700 text-lg mb-6 leading-relaxed">{startup.description}</p>
                        
                        {/* Match Reason & Calibration Info */}
                        <div className="mb-6 space-y-3">
                          <div className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                            <p className="text-blue-800 font-medium">
                              💡 {startup.match_reason}
                            </p>
                          </div>
                          
                          <div className="p-4 bg-gray-50 rounded-lg border-l-4 border-gray-400">
                            <div className="text-gray-700 text-sm">
                              <div className="font-medium mb-2">📊 Calibration Details:</div>
                              <div className="grid grid-cols-3 gap-4 text-xs">
                                <div>
                                  <span className="font-medium">Z-Score:</span>
                                  <div className={`font-bold ${
                                    Math.abs(startup.calibration_info.z_score) > 2 ? 'text-green-600' :
                                    Math.abs(startup.calibration_info.z_score) > 1 ? 'text-yellow-600' : 'text-red-600'
                                  }`}>
                                    {startup.calibration_info.z_score}
                                  </div>
                                </div>
                                <div>
                                  <span className="font-medium">Background μ:</span>
                                  <div className="text-gray-600">{startup.calibration_info.background_mean}</div>
                                </div>
                                <div>
                                  <span className="font-medium">Background σ:</span>
                                  <div className="text-gray-600">{startup.calibration_info.background_std}</div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                          <div className="bg-blue-50 p-4 rounded-lg">
                            <span className="font-semibold text-blue-600 block mb-2">Industry</span>
                            <p className="text-gray-900 font-medium">{startup.industry}</p>
                          </div>
                          <div className="bg-green-50 p-4 rounded-lg">
                            <span className="font-semibold text-green-600 block mb-2">Location</span>
                            <p className="text-gray-900 font-medium">{startup.location}</p>
                          </div>
                          <div className="bg-purple-50 p-4 rounded-lg">
                            <span className="font-semibold text-purple-600 block mb-2">Funding</span>
                            <p className="text-gray-900 font-medium">{startup.funding}</p>
                          </div>
                          <div className="bg-orange-50 p-4 rounded-lg">
                            <span className="font-semibold text-orange-600 block mb-2">Team Size</span>
                            <p className="text-gray-900 font-medium">{startup.team_size} people</p>
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
              <div className="space-y-6">
                {/* Q&A Input */}
                <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 text-center">
                  <h2 className="text-3xl font-bold text-gray-900 mb-6">Ask Questions</h2>
                  <div className="flex gap-4 max-w-2xl mx-auto">
                    <input
                      type="text"
                      value={qaQuery}
                      onChange={(e) => setQaQuery(e.target.value)}
                      placeholder="e.g., What are the most funded AI startups? Which startups are in healthcare?"
                      className="flex-1 px-6 py-4 border border-gray-300 rounded-lg focus:ring-4 focus:ring-blue-200 focus:border-blue-500 text-lg transition-all duration-300"
                      onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
                    />
                    <button
                      onClick={handleAsk}
                      disabled={loading}
                      className="px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                    >
                      {loading ? '🤔 Thinking...' : 'Ask'}
                    </button>
                  </div>
                </div>

                {/* Q&A Response */}
                {qaResponse && (
                  <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3 text-center">Question</h3>
                      <p className="text-gray-700 italic text-lg text-center bg-gray-50 p-4 rounded-lg">"{qaResponse.question}"</p>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-3 text-center">Answer</h3>
                      <p className="text-gray-700 leading-relaxed text-lg bg-blue-50 p-6 rounded-lg">{qaResponse.answer}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
  )
}

export default App
