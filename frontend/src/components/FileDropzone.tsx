'use client'

import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'
import { Upload, FileText, X } from 'lucide-react'

interface FileDropzoneProps {
  file: File | null
  onFileSelected: (file: File | null) => void
  onError?: (message: string) => void
  accept?: string
  maxSizeMb?: number
}

export function FileDropzone({
  file,
  onFileSelected,
  onError,
  accept = '.pdf',
  maxSizeMb = 50,
}: FileDropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const maxBytes = maxSizeMb * 1024 * 1024

  const validateAndSelectFile = (candidate: File | null) => {
    if (!candidate) {
      return
    }

    const isPdf = candidate.type === 'application/pdf' || candidate.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      onError?.('Please upload a valid PDF file.')
      return
    }

    if (candidate.size > maxBytes) {
      onError?.(`PDF is too large. Maximum allowed size is ${maxSizeMb} MB.`)
      return
    }

    onError?.('')
    onFileSelected(candidate)
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragOver(false)
    validateAndSelectFile(event.dataTransfer.files?.[0] ?? null)
  }

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => {
    setIsDragOver(false)
  }

  const handleBrowse = () => {
    inputRef.current?.click()
  }

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    validateAndSelectFile(event.target.files?.[0] ?? null)
    event.target.value = ''
  }

  const clearSelectedFile = () => {
    onFileSelected(null)
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleBrowse}
      className={[
        'relative border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer',
        isDragOver
          ? 'border-[#1561AD] bg-[#1561AD]/5'
          : file
            ? 'border-[#7EBC59] bg-[#7EBC59]/5'
            : 'border-border hover:border-[#F7882F]/50 hover:bg-[#F7882F]/5',
      ].join(' ')}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleInputChange}
        className="hidden"
      />

      {file ? (
        <div className="flex items-center justify-center gap-3">
          <FileText className="h-8 w-8 text-[#7EBC59]" />
          <div className="text-left">
            <p className="font-medium text-foreground">{file.name}</p>
            <p className="text-sm text-muted-foreground">
              {(file.size / (1024 * 1024)).toFixed(1)} MB
            </p>
          </div>
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation()
              clearSelectedFile()
            }}
            className="ml-2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Remove selected file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <>
          <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
          <p className="text-base font-medium text-foreground">Drop your PDF here</p>
          <p className="text-sm text-muted-foreground mt-1">or click to browse</p>
          <p className="text-xs text-muted-foreground mt-2">Max size: {maxSizeMb} MB</p>
        </>
      )}
    </div>
  )
}
