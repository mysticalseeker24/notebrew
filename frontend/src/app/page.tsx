import { Navbar } from '@/components/Navbar'
import { Hero } from '@/components/Hero'
import { UploadCard } from '@/components/UploadCard'
import { HowItWorks } from '@/components/HowItWorks'
import { Footer } from '@/components/Footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <Hero />

      {/* Upload Section — overlaps with hero bottom */}
      <section className="-mt-20 relative z-10 px-6 pb-16">
        <UploadCard />
      </section>

      <HowItWorks />
      <Footer />
    </main>
  )
}
