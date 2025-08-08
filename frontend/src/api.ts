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
  rank: number
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
