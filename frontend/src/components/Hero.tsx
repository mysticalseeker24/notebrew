'use client'

import { motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'

export function Hero() {
    return (
        <section className="min-h-screen flex flex-col items-center justify-center px-6 pt-16">
            <div className="max-w-3xl mx-auto text-center">
                {/* Main Title */}
                <motion.h1
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
                    className="text-5xl md:text-7xl font-black tracking-tight text-[#202020] leading-[1.1]"
                >
                    Brew Research Papers
                    <br />
                    <span className="text-[#1561AD]">into Notebooks</span>
                </motion.h1>

                {/* Subtitle */}
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }}
                    className="mt-6 text-lg md:text-xl text-muted-foreground max-w-xl mx-auto leading-relaxed"
                >
                    Drop any research paper and our AI agent brews it into a
                    runnable Jupyter notebook — with real PyTorch code.
                </motion.p>

                {/* Tech badges */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.5 }}
                    className="mt-4 flex items-center justify-center gap-3 text-xs text-muted-foreground"
                >
                    <span className="px-2 py-1 rounded-full bg-[#EDE0C8] border border-border">
                        Gemini 3 Flash Vision
                    </span>
                    <span className="px-2 py-1 rounded-full bg-[#EDE0C8] border border-border">
                        PyMuPDF4LLM
                    </span>
                    <span className="px-2 py-1 rounded-full bg-[#EDE0C8] border border-border">
                        PyTorch
                    </span>
                </motion.div>
            </div>

            {/* Scroll indicator */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1, duration: 0.5 }}
                className="absolute bottom-8"
            >
                <ChevronDown className="w-6 h-6 text-muted-foreground animate-gentle-bounce" />
            </motion.div>
        </section>
    )
}
