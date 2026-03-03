'use client'

import { useState } from 'react'
import { Upload, Link, Download, Loader2 } from 'lucide-react'
import { processArxiv, uploadPDF, checkStatus, downloadNotebook } from '@/lib/api'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'pdf' | 'arxiv'>('pdf')
  const [arxivUrl, setArxivUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const handleArxivSubmit = async () => {
    if (!arxivUrl) return
    
    setProcessing(true)
    setError('')
    
    try {
      const response = await processArxiv(arxivUrl)
      setTaskId(response.task_id)
      pollStatus(response.task_id)
    } catch (err: any) {
      setError(err.message || 'Failed to process arXiv paper')
      setProcessing(false)
    }
  }

  const handlePDFUpload = async () => {
    if (!file) return
    
    setProcessing(true)
    setError('')
    
    try {
      const response = await uploadPDF(file)
      setTaskId(response.task_id)
      pollStatus(response.task_id)
    } catch (err: any) {
      setError(err.message || 'Failed to upload PDF')
      setProcessing(false)
    }
  }

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await checkStatus(id)
        setProgress(statusResponse.progress)
        setStatus(statusResponse.message)
        
        if (statusResponse.status === 'completed') {
          clearInterval(interval)
          setProcessing(false)
        } else if (statusResponse.status === 'failed') {
          clearInterval(interval)
          setProcessing(false)
          setError(statusResponse.message)
        }
      } catch (err) {
        clearInterval(interval)
        setProcessing(false)
      }
    }, 2000)
  }

  const handleDownload = async () => {
    if (!taskId) return
    
    try {
      await downloadNotebook(taskId)
    } catch (err: any) {
      setError(err.message || 'Failed to download notebook')
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Paper2Notebook 📄→📓
          </h1>
          <p className="text-xl text-gray-600">
            Transform research papers into executable Jupyter notebooks
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Powered by Gemini 3 Flash Preview & MiniMax M2.5
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Tabs */}
          <div className="flex gap-4 mb-8">
            <button
              onClick={() => setActiveTab('pdf')}
              className={`flex-1 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'pdf'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Upload className="inline mr-2" size={20} />
              Upload PDF
            </button>
            <button
              onClick={() => setActiveTab('arxiv')}
              className={`flex-1 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'arxiv'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Link className="inline mr-2" size={20} />
              arXiv URL
            </button>
          </div>

          {/* Content */}
          {activeTab === 'pdf' ? (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="mx-auto mb-4 text-gray-400" size={48} />
                  <p className="text-lg font-medium text-gray-700">
                    {file ? file.name : 'Drop your PDF here or click to browse'}
                  </p>
                </label>
              </div>
              <button
                onClick={handlePDFUpload}
                disabled={!file || processing}
                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {processing ? 'Processing...' : 'Generate Notebook'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type="text"
                placeholder="https://arxiv.org/abs/2301.00001 or 2301.00001"
                value={arxivUrl}
                onChange={(e) => setArxivUrl(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={handleArxivSubmit}
                disabled={!arxivUrl || processing}
                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {processing ? 'Processing...' : 'Generate Notebook'}
              </button>
            </div>
          )}

          {/* Progress */}
          {processing && (
            <div className="mt-8 space-y-4">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>{status}</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* Download */}
          {taskId && !processing && !error && (
            <div className="mt-8 p-6 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium mb-4">
                ✅ Notebook generated successfully!
              </p>
              <button
                onClick={handleDownload}
                className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 flex items-center justify-center gap-2"
              >
                <Download size={20} />
                Download Notebook
              </button>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            icon="🐍"
            title="PyTorch Code"
            description="Real ML implementations scaled for CPU execution"
          />
          <FeatureCard
            icon="📐"
            title="LaTeX Extraction"
            description="Automatically extracts and renders equations"
          />
          <FeatureCard
            icon="☁️"
            title="Colab Ready"
            description="One-click 'Open in Colab' functionality"
          />
        </div>
      </div>
    </main>
  )
}

function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-md">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="font-semibold text-lg text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}
