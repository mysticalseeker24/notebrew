import { Navbar } from '@/components/Navbar'
import { HowItWorks } from '@/components/HowItWorks'
import { Footer } from '@/components/Footer'

export default function FeaturesPage() {
    return (
        <main className="min-h-screen bg-background">
            <Navbar />

            {/* Page Header */}
            <section className="pt-28 pb-8 px-6">
                <div className="max-w-5xl mx-auto text-center">
                    <h1 className="text-4xl md:text-5xl font-black tracking-tight text-[#202020]">
                        Features
                    </h1>
                    <p className="mt-3 text-lg text-muted-foreground max-w-lg mx-auto">
                        Everything that makes NoteBrew powerful
                    </p>
                </div>
            </section>

            <HowItWorks />

            {/* Technical Details */}
            <section className="py-16 px-6">
                <div className="max-w-4xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* AI Stack */}
                        <div className="p-6 rounded-xl bg-card border border-border/60">
                            <h3 className="text-lg font-bold text-[#202020] mb-3">🧠 AI Stack</h3>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li className="flex items-start gap-2">
                                    <span className="text-[#1561AD] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">Gemini 3 Flash Vision</strong> — PDF structure, equations, tables, figures</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-[#1561AD] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">PyMuPDF4LLM</strong> — Full text extraction, zero cost</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-[#1561AD] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">MiniMax M2.5</strong> — Cost-effective fallback model</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-[#1561AD] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">OpenRouter</strong> — Unified LLM API access</span>
                                </li>
                            </ul>
                        </div>

                        {/* Output */}
                        <div className="p-6 rounded-xl bg-card border border-border/60">
                            <h3 className="text-lg font-bold text-[#202020] mb-3">📓 Notebook Output</h3>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li className="flex items-start gap-2">
                                    <span className="text-[#F7882F] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">PyTorch code</strong> — Real implementations, CPU-scaled</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-[#F7882F] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">LaTeX equations</strong> — Extracted and rendered in markdown</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-[#F7882F] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">Google Colab</strong> — One-click open</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-[#F7882F] mt-0.5">▸</span>
                                    <span><strong className="text-foreground">Kaggle</strong> — Direct kernel launch</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <Footer />
        </main>
    )
}
