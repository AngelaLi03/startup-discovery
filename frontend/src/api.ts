import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export interface Startup {
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

export interface QAResponse {
  question: string
  answer: string
}

export const searchStartups = async (query: string): Promise<Startup[]> => {
  try {
    const response = await api.get('/search', {
      params: { q: query }
    })
    return response.data
  } catch (error) {
    console.error('Search API error:', error)
    throw new Error('Failed to search startups')
  }
}

export const askQuestion = async (question: string): Promise<QAResponse> => {
  try {
    const response = await api.get('/ask', {
      params: { q: question }
    })
    return response.data
  } catch (error) {
    console.error('Q&A API error:', error)
    throw new Error('Failed to get answer')
  }
}

export const checkHealth = async (): Promise<{ status: string; index_loaded: boolean }> => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check error:', error)
    throw new Error('Failed to check API health')
  }
}
