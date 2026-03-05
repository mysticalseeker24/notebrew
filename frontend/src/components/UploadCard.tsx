'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Upload, Link as LinkIcon, AlertTriangle } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { processArxiv, uploadPDF } from '@/lib/api'
import { ScrollReveal } from '@/components/ScrollReveal'
import { FileDropzone } from '@/components/FileDropzone'

export function UploadCard() {
    const router = useRouter()
    const [file, setFile] = useState<File | null>(null)
    const [arxivUrl, setArxivUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const validateArxivInput = (value: string): boolean => {
        const normalized = value.trim()
        if (!normalized) {
            setError('Please enter an arXiv URL or ID.')
            return false
        }

        const maybeUrl = /^https?:\/\//i.test(normalized)
        if (maybeUrl && !normalized.includes('arxiv.org')) {
            setError('URL must point to arxiv.org.')
            return false
        }

        setError('')
        return true
    }

    const handlePDFSubmit = async () => {
        if (!file) {
            setError('Please select a PDF before brewing.')
            return
        }

        setLoading(true)
        setError('')
        try {
            const response = await uploadPDF(file)
            router.push(`/brew/${response.task_id}`)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to upload PDF')
            setLoading(false)
        }
    }

    const handleArxivSubmit = async () => {
        if (!validateArxivInput(arxivUrl)) {
            return
        }

        setLoading(true)
        setError('')
        try {
            const response = await processArxiv(arxivUrl.trim())
            router.push(`/brew/${response.task_id}`)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to process arXiv paper')
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
                            <FileDropzone
                                file={file}
                                onFileSelected={setFile}
                                onError={setError}
                                maxSizeMb={50}
                            />

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
                                onChange={(e) => {
                                    setArxivUrl(e.target.value)
                                    if (error) {
                                        setError('')
                                    }
                                }}
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
                            className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 flex items-start gap-2"
                        >
                            <AlertTriangle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-destructive">{error}</p>
                        </motion.div>
                    )}
                </CardContent>
            </Card>
        </ScrollReveal>
    )
}
