import api from './index'
import { postSse } from './sse'

export interface QARequest {
  query: string
  top_k?: number
  stream?: boolean
}

export interface ArticleSource {
  id: number
  standard_id: number
  chapter: string
  section: string
  category: string
  text: string
  score: number
  formulas: string[]
}

export interface QAResponseData {
  answer: string
  query: string
  sources: ArticleSource[]
  source_count: number
}

export interface QAResponse {
  code: number
  message: string
  data: QAResponseData
}

export const qaApi = {
  ask: async (request: QARequest): Promise<QAResponse> => {
    return await api.post('/v1/qa', request)
  },

  askStream: (request: QARequest, signal?: AbortSignal) => {
    const baseUrl = import.meta.env.VITE_API_URL || '/api'
    return postSse(`${baseUrl}/v1/qa/stream`, request, signal)
  },
}
