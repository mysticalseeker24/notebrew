'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
    FileSearch, Brain, Code, CheckCircle, BookOpen, Loader2,
    Download, ExternalLink, ArrowLeft
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'
import { checkStatus, downloadNotebook, type ProgressResponse } from '@/lib/api'

/* ─── Step definitions ─── */
const STEPS = [
    { key: 'parse', label: 'Parsing paper', icon: FileSearch },
    { key: 'plan_notebook', label: 'Planning notebook', icon: Brain },
    { key: 'generate_code', label: 'Generating code', icon: Code },
    { key: 'validate_code', label: 'Validating code', icon: CheckCircle },
    { key: 'assemble_notebook', label: 'Assembling notebook', icon: BookOpen },
]

function getStepIndex(tool: string): number {
    const normalized = tool.toLowerCase()
    const idx = STEPS.findIndex(s => normalized.includes(s.key))
    return idx >= 0 ? idx : 0
}

/* ─── Main Page ─── */
export default function BrewPage() {
    const params = useParams()
    const router = useRouter()
    const taskId = params.id as string

    const [status, setStatus] = useState<'brewing' | 'completed' | 'failed'>('brewing')
    const [progress, setProgress] = useState(0)
    const [message, setMessage] = useState('Starting brew...')
    const [currentTool, setCurrentTool] = useState('')
    const [error, setError] = useState('')
    const [launchLinks, setLaunchLinks] = useState<Pick<
        ProgressResponse,
        'notebook_url' | 'colab_url' | 'kaggle_url' | 'links_ready' | 'links_message'
    >>({
        notebook_url: undefined,
        colab_url: undefined,
        kaggle_url: undefined,
        links_ready: false,
        links_message: undefined,
    })

    /* ─── Poll for status ─── */
    useEffect(() => {
        if (!taskId) return

        const interval = setInterval(async () => {
            try {
                const res = await checkStatus(taskId)
                setProgress(res.progress)
                setMessage(res.message)
                setCurrentTool(res.current_tool || '')
                setLaunchLinks({
                    notebook_url: res.notebook_url,
                    colab_url: res.colab_url,
                    kaggle_url: res.kaggle_url,
                    links_ready: res.links_ready,
                    links_message: res.links_message,
                })

                if (res.status === 'completed') {
                    setStatus('completed')
                    clearInterval(interval)
                } else if (res.status === 'failed') {
                    setStatus('failed')
                    setError(res.message)
                    clearInterval(interval)
                }
            } catch {
                setStatus('failed')
                setError('Lost connection to the server')
                clearInterval(interval)
            }
        }, 2000)

        return () => clearInterval(interval)
    }, [taskId])

    const activeStep = getStepIndex(currentTool)

    return (
        <main className="min-h-screen bg-background flex flex-col">
            <Navbar />

            <div className="flex-1 pt-24 pb-16 px-6">
                <div className="max-w-2xl mx-auto">
                    {/* Back button */}
                    <button
                        onClick={() => router.push('/')}
                        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back home
                    </button>

                    <AnimatePresence mode="wait">
                        {status === 'brewing' && (
                            <BrewingView
                                progress={progress}
                                message={message}
                                currentTool={currentTool}
                                activeStep={activeStep}
                            />
                        )}
                        {status === 'completed' && (
                            <CompletedView taskId={taskId} launchLinks={launchLinks} />
                        )}
                        {status === 'failed' && (
                            <FailedView error={error} onRetry={() => router.push('/')} />
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <Footer />
        </main>
    )
}

/* ═══════════════════════════════════════════
   Brewing State
   ═══════════════════════════════════════════ */
function BrewingView({
    progress, message, currentTool, activeStep
}: {
    progress: number; message: string; currentTool: string; activeStep: number
}) {
    return (
        <motion.div
            key="brewing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="text-center"
        >
            {/* Coffee icon */}
            <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                className="text-6xl mb-6"
            >
                ☕
            </motion.div>

            <h1 className="text-3xl font-black text-[#202020] mb-2">
                Brewing your notebook...
            </h1>
            <p className="text-muted-foreground mb-8">{message}</p>

            {/* Progress bar */}
            <div className="mb-2">
                <Progress value={progress} className="h-3 bg-[#EDE0C8]" />
            </div>
            <p className="text-sm text-muted-foreground mb-10">
                {Math.round(progress)}% complete
            </p>

            {/* Step Timeline */}
            <Card className="bg-card border-border/60 text-left">
                <CardContent className="p-6">
                    <div className="space-y-4">
                        {STEPS.map((step, i) => {
                            const isComplete = i < activeStep
                            const isActive = i === activeStep
                            const isPending = i > activeStep
                            const StepIcon = step.icon

                            return (
                                <div key={step.key} className="flex items-center gap-4">
                                    {/* Icon */}
                                    <div className={`
                    flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                    ${isComplete ? 'bg-[#7EBC59] text-white' : ''}
                    ${isActive ? 'bg-[#1561AD] text-white' : ''}
                    ${isPending ? 'bg-[#EDE0C8] text-muted-foreground' : ''}
                  `}>
                                        {isComplete ? (
                                            <CheckCircle className="h-4 w-4" />
                                        ) : isActive ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <StepIcon className="h-4 w-4" />
                                        )}
                                    </div>

                                    {/* Label */}
                                    <span className={`text-sm font-medium ${isComplete ? 'text-[#7EBC59]' :
                                            isActive ? 'text-[#1561AD] font-semibold' :
                                                'text-muted-foreground'
                                        }`}>
                                        {step.label}
                                    </span>

                                    {/* Connector line */}
                                    {i < STEPS.length - 1 && (
                                        <div className="flex-1 border-t border-dashed border-border" />
                                    )}
                                </div>
                            )
                        })}
                    </div>

                    {currentTool && (
                        <p className="mt-4 pt-4 border-t border-border text-xs text-muted-foreground">
                            Agent tool: <code className="font-mono text-[#1561AD]">{currentTool}</code>
                        </p>
                    )}
                </CardContent>
            </Card>
        </motion.div>
    )
}

/* ═══════════════════════════════════════════
   Completed State
   ═══════════════════════════════════════════ */
function CompletedView({
    taskId,
    launchLinks,
}: {
    taskId: string
    launchLinks: Pick<ProgressResponse, 'notebook_url' | 'colab_url' | 'kaggle_url' | 'links_ready' | 'links_message'>
}) {
    const [downloadError, setDownloadError] = useState('')

    const handleDownload = async () => {
        try {
            setDownloadError('')
            await downloadNotebook(taskId)
        } catch (error) {
            setDownloadError(error instanceof Error ? error.message : 'Failed to download notebook')
        }
    }

    const colabUrl = launchLinks.colab_url || 'https://colab.research.google.com/#create=true'
    const kaggleUrl = launchLinks.kaggle_url || 'https://www.kaggle.com/code/new'

    return (
        <motion.div
            key="completed"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="text-center"
        >
            {/* Success icon */}
            <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 10, delay: 0.2 }}
                className="text-6xl mb-6"
            >
                🎉
            </motion.div>

            <h1 className="text-3xl font-black text-[#202020] mb-2">
                Notebook brewed!
            </h1>
            <p className="text-muted-foreground mb-10">
                Your research paper has been transformed into an executable Jupyter notebook.
            </p>

            {launchLinks.links_message && (
                <p className={`mb-6 text-sm ${launchLinks.links_ready ? 'text-[#1561AD]' : 'text-muted-foreground'}`}>
                    {launchLinks.links_message}
                </p>
            )}

            {/* Action Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-lg mx-auto">
                <Button
                    onClick={handleDownload}
                    className="h-14 flex flex-col items-center justify-center gap-1 bg-[#1561AD] hover:bg-[#124e8f] text-white shadow-md"
                >
                    <Download className="h-5 w-5" />
                    <span className="text-xs font-grotesk">Download .ipynb</span>
                </Button>

                <a href={colabUrl} target="_blank" rel="noopener noreferrer">
                    <Button
                        variant="outline"
                        className="w-full h-14 flex flex-col items-center justify-center gap-1 border-[#F7882F] text-[#F7882F] hover:bg-[#F7882F] hover:text-white shadow-md"
                    >
                        <ExternalLink className="h-5 w-5" />
                        <span className="text-xs font-grotesk">Open in Colab</span>
                    </Button>
                </a>

                <a href={kaggleUrl} target="_blank" rel="noopener noreferrer">
                    <Button
                        variant="outline"
                        className="w-full h-14 flex flex-col items-center justify-center gap-1 border-[#20BEFF] text-[#20BEFF] hover:bg-[#20BEFF] hover:text-white shadow-md"
                    >
                        <ExternalLink className="h-5 w-5" />
                        <span className="text-xs font-grotesk">Open in Kaggle</span>
                    </Button>
                </a>
            </div>

            {downloadError && (
                <p className="mt-4 text-sm text-destructive">{downloadError}</p>
            )}

            {/* Brew another */}
            <div className="mt-8">
                <a
                    href="/"
                    className="text-sm text-muted-foreground hover:text-[#1561AD] transition-colors"
                >
                    ☕ Brew another paper
                </a>
            </div>
        </motion.div>
    )
}

/* ═══════════════════════════════════════════
   Failed State
   ═══════════════════════════════════════════ */
function FailedView({ error, onRetry }: { error: string; onRetry: () => void }) {
    return (
        <motion.div
            key="failed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
        >
            <div className="text-6xl mb-6">😞</div>
            <h1 className="text-3xl font-black text-[#202020] mb-2">
                Brew failed
            </h1>
            <p className="text-destructive mb-8">{error}</p>
            <Button
                onClick={onRetry}
                className="bg-[#F7882F] hover:bg-[#e57a24] text-white font-grotesk"
            >
                ☕ Try again
            </Button>
        </motion.div>
    )
}
