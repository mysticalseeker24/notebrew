import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface NotebookResponse {
  task_id: string
  status: string
  notebook_url?: string
  error?: string
}

export interface ProgressResponse {
  task_id: string
  status: string
  progress: number
  message: string
  current_tool?: string
  current_section?: string
  notebook_url?: string
  colab_url?: string
  kaggle_url?: string
  links_ready?: boolean
  links_message?: string
}

function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (typeof error.response?.data?.message === 'string' && error.response.data.message.trim()) {
      return error.response.data.message
    }
    if (error.message) {
      return error.message
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return fallback
}

export const uploadPDF = async (file: File, model?: string): Promise<NotebookResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  if (model) formData.append('model', model)

  try {
    const response = await api.post('/api/upload-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to upload PDF'))
  }
}

export const processArxiv = async (arxivUrl: string, model?: string): Promise<NotebookResponse> => {
  try {
    const response = await api.post('/api/arxiv', {
      arxiv_url: arxivUrl,
      model,
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to process arXiv paper'))
  }
}

export const checkStatus = async (taskId: string): Promise<ProgressResponse> => {
  try {
    const response = await api.get(`/api/status/${taskId}`)
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to fetch task status'))
  }
}

export const downloadNotebook = async (taskId: string): Promise<void> => {
  try {
    const response = await api.get(`/api/download/${taskId}`, {
      responseType: 'blob',
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `notebrew_${taskId}.ipynb`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    throw new Error(getApiErrorMessage(error, 'Failed to download notebook'))
  }
}
