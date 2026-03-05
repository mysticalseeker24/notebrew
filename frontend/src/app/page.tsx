import { Navbar } from '@/components/Navbar'
import { Hero } from '@/components/Hero'
import { UploadCard } from '@/components/UploadCard'
import { Footer } from '@/components/Footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <Hero />

      {/* Upload Section — overlaps with hero bottom */}
      <section className="-mt-20 relative z-10 px-6 pb-24">
        <UploadCard />
      </section>

      <Footer />
    </main>
  )
}
