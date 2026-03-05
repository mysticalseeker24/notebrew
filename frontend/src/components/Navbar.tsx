'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

export function Navbar() {
    return (
        <motion.nav
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-[#FCEED1]/80 border-b border-border/50"
        >
            <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-2">
                    <span className="text-2xl font-black tracking-tight text-[#202020]">
                        NoteBrew
                    </span>
                    <span className="text-xl">☕</span>
                </Link>

                {/* Nav Links */}
                <div className="flex items-center gap-8">
                    <Link
                        href="/features"
                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Features
                    </Link>
                    <a
                        href="https://github.com/mysticalseeker24/notebrew"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        GitHub
                    </a>
                </div>
            </div>
        </motion.nav>
    )
}
