import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
  current_section?: string
}

export const uploadPDF = async (file: File, model?: string): Promise<NotebookResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  if (model) formData.append('model', model)

  const response = await api.post('/api/upload-pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export const processArxiv = async (arxivUrl: string, model?: string): Promise<NotebookResponse> => {
  const response = await api.post('/api/arxiv', {
    arxiv_url: arxivUrl,
    model,
  })

  return response.data
}

export const checkStatus = async (taskId: string): Promise<ProgressResponse> => {
  const response = await api.get(`/api/status/${taskId}`)
  return response.data
}

export const downloadNotebook = async (taskId: string): Promise<void> => {
  const response = await api.get(`/api/download/${taskId}`, {
    responseType: 'blob',
  })

  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `paper_notebook_${taskId}.ipynb`)
  document.body.appendChild(link)
  link.click()
  link.remove()
}
