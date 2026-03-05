import { Github } from 'lucide-react'

export function Footer() {
    return (
        <footer className="border-t border-border/50 py-8 px-6">
            <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="font-bold text-foreground">NoteBrew</span>
                    <span>☕</span>
                    <span>·</span>
                    <span>v2.2.0</span>
                </div>

                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>
                        Built by{' '}
                        <a
                            href="https://github.com/mysticalseeker24"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-foreground hover:text-[#1561AD] transition-colors"
                        >
                            Saksham Mishra
                        </a>
                    </span>
                    <a
                        href="https://github.com/mysticalseeker24/notebrew"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-foreground transition-colors"
                    >
                        <Github className="h-4 w-4" />
                    </a>
                </div>
            </div>
        </footer>
    )
}
