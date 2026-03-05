'use client'

import { FileSearch, Brain, Code, CheckCircle, BookOpen, CloudUpload } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollReveal } from '@/components/ScrollReveal'

const steps = [
    {
        number: '01',
        icon: FileSearch,
        title: 'Parse Paper',
        description: 'Gemini Vision extracts equations, tables, figures & structure. PyMuPDF4LLM captures full text.',
    },
    {
        number: '02',
        icon: Brain,
        title: 'Plan Notebook',
        description: 'AI agent analyzes the paper and designs an optimal notebook structure with sections.',
    },
    {
        number: '03',
        icon: Code,
        title: 'Generate Code',
        description: 'Produces PyTorch implementations scaled for CPU execution, with explanations.',
    },
    {
        number: '04',
        icon: CheckCircle,
        title: 'Validate Code',
        description: 'Syntax checking and import validation. Retries automatically on errors.',
    },
    {
        number: '05',
        icon: BookOpen,
        title: 'Assemble Notebook',
        description: 'Builds a structured .ipynb with markdown cells, code cells, and LaTeX equations.',
    },
    {
        number: '06',
        icon: CloudUpload,
        title: 'Export Anywhere',
        description: 'Download the notebook, open in Google Colab, or launch directly in Kaggle.',
    },
]

export function HowItWorks() {
    return (
        <section id="features" className="py-24 px-6">
            <div className="max-w-5xl mx-auto">
                {/* Section Header */}
                <ScrollReveal>
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-black tracking-tight text-[#202020]">
                            How NoteBrew Works
                        </h2>
                        <p className="mt-3 text-lg text-muted-foreground max-w-lg mx-auto">
                            From paper to notebook in 6 intelligent steps
                        </p>
                    </div>
                </ScrollReveal>

                {/* Step Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {steps.map((step, i) => (
                        <ScrollReveal key={step.number} delay={i * 0.1}>
                            <Card className="group border-border/60 bg-card hover:shadow-lg hover:-translate-y-1 transition-all duration-300 h-full">
                                <CardContent className="p-6">
                                    {/* Step number */}
                                    <div className="flex items-center justify-between mb-4">
                                        <span className="text-xs font-mono font-bold text-[#F7882F] tracking-wider">
                                            STEP {step.number}
                                        </span>
                                        <step.icon className="h-5 w-5 text-[#1561AD] group-hover:text-[#F7882F] transition-colors" />
                                    </div>

                                    {/* Content */}
                                    <h3 className="text-lg font-bold text-[#202020] mb-2">
                                        {step.title}
                                    </h3>
                                    <p className="text-sm text-muted-foreground leading-relaxed">
                                        {step.description}
                                    </p>
                                </CardContent>
                            </Card>
                        </ScrollReveal>
                    ))}
                </div>
            </div>
        </section>
    )
}
