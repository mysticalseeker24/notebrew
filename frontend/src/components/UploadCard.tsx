'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Upload, Link as LinkIcon, FileText } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { processArxiv, uploadPDF } from '@/lib/api'
import { ScrollReveal } from '@/components/ScrollReveal'

export function UploadCard() {
    const router = useRouter()
    const [file, setFile] = useState<File | null>(null)
    const [arxivUrl, setArxivUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [isDragOver, setIsDragOver] = useState(false)

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile?.type === 'application/pdf') {
            setFile(droppedFile)
            setError('')
        } else {
            setError('Please drop a PDF file')
        }
    }, [])

    const handlePDFSubmit = async () => {
        if (!file) return
        setLoading(true)
        setError('')
        try {
            const response = await uploadPDF(file)
            router.push(`/brew/${response.task_id}`)
        } catch (err: any) {
            setError(err.message || 'Failed to upload PDF')
            setLoading(false)
        }
    }

    const handleArxivSubmit = async () => {
        if (!arxivUrl) return
        setLoading(true)
        setError('')
        try {
            const response = await processArxiv(arxivUrl)
            router.push(`/brew/${response.task_id}`)
        } catch (err: any) {
            setError(err.message || 'Failed to process arXiv paper')
            setLoading(false)
        }
    }

    return (
        <ScrollReveal>
            <Card className="max-w-2xl mx-auto border-border/60 shadow-lg bg-card">
                <CardContent className="p-8">
                    <Tabs defaultValue="pdf" className="w-full">
                        <TabsList className="grid w-full grid-cols-2 mb-6 bg-[#EDE0C8]">
                            <TabsTrigger
                                value="pdf"
                                className="font-grotesk font-medium data-[state=active]:bg-[#FCEED1] data-[state=active]:shadow-sm"
                            >
                                <Upload className="mr-2 h-4 w-4" />
                                Upload PDF
                            </TabsTrigger>
                            <TabsTrigger
                                value="arxiv"
                                className="font-grotesk font-medium data-[state=active]:bg-[#FCEED1] data-[state=active]:shadow-sm"
                            >
                                <LinkIcon className="mr-2 h-4 w-4" />
                                arXiv URL
                            </TabsTrigger>
                        </TabsList>

                        {/* PDF Upload Tab */}
                        <TabsContent value="pdf" className="space-y-4">
                            <div
                                onDrop={handleDrop}
                                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
                                onDragLeave={() => setIsDragOver(false)}
                                className={`
                  relative border-2 border-dashed rounded-xl p-10 text-center
                  transition-all duration-200 cursor-pointer
                  ${isDragOver
                                        ? 'border-[#1561AD] bg-[#1561AD]/5'
                                        : file
                                            ? 'border-[#7EBC59] bg-[#7EBC59]/5'
                                            : 'border-border hover:border-[#F7882F]/50 hover:bg-[#F7882F]/5'
                                    }
                `}
                            >
                                <input
                                    type="file"
                                    accept=".pdf"
                                    onChange={(e) => {
                                        setFile(e.target.files?.[0] || null)
                                        setError('')
                                    }}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    id="file-upload"
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
                                    </div>
                                ) : (
                                    <>
                                        <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
                                        <p className="text-base font-medium text-foreground">
                                            Drop your PDF here
                                        </p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            or click to browse
                                        </p>
                                    </>
                                )}
                            </div>

                            <Button
                                onClick={handlePDFSubmit}
                                disabled={!file || loading}
                                className="w-full h-12 text-base font-grotesk font-semibold bg-[#F7882F] hover:bg-[#e57a24] text-white shadow-md hover:shadow-lg transition-all"
                            >
                                {loading ? (
                                    <span className="flex items-center gap-2">
                                        <motion.span
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                            className="inline-block"
                                        >
                                            ☕
                                        </motion.span>
                                        Brewing...
                                    </span>
                                ) : (
                                    '☕ Brew Notebook'
                                )}
                            </Button>
                        </TabsContent>

                        {/* arXiv URL Tab */}
                        <TabsContent value="arxiv" className="space-y-4">
                            <input
                                type="text"
                                placeholder="https://arxiv.org/abs/2301.00001 or just 2301.00001"
                                value={arxivUrl}
                                onChange={(e) => setArxivUrl(e.target.value)}
                                className="w-full px-4 py-3 rounded-xl border border-border bg-[#FCEED1]
                  focus:ring-2 focus:ring-[#1561AD]/30 focus:border-[#1561AD]
                  outline-none transition-all text-foreground placeholder:text-muted-foreground"
                            />

                            <Button
                                onClick={handleArxivSubmit}
                                disabled={!arxivUrl || loading}
                                className="w-full h-12 text-base font-grotesk font-semibold bg-[#F7882F] hover:bg-[#e57a24] text-white shadow-md hover:shadow-lg transition-all"
                            >
                                {loading ? (
                                    <span className="flex items-center gap-2">
                                        <motion.span
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                            className="inline-block"
                                        >
                                            ☕
                                        </motion.span>
                                        Brewing...
                                    </span>
                                ) : (
                                    '☕ Brew Notebook'
                                )}
                            </Button>
                        </TabsContent>
                    </Tabs>

                    {/* Error */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20"
                        >
                            <p className="text-sm text-destructive">{error}</p>
                        </motion.div>
                    )}
                </CardContent>
            </Card>
        </ScrollReveal>
    )
}
