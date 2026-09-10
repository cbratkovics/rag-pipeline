import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/components/QueryProvider'
import { Analytics } from '@vercel/analytics/react'

export const metadata: Metadata = {
  title: 'Production RAG Pipeline | AI Engineering Demo',
  description:
    'Enterprise-grade RAG system with A/B testing, RAGAS evaluation, and hybrid retrieval. Built with FastAPI, ChromaDB, and Next.js.',
  keywords: [
    'RAG',
    'AI Engineering',
    'A/B Testing',
    'RAGAS',
    'Vector Search',
    'BM25',
    'Machine Learning',
    'NLP',
  ],
  authors: [{ name: 'Christopher Bratkovics', url: 'https://github.com/cbratkovics' }],
  openGraph: {
    title: 'Production RAG Pipeline',
    description: 'Enterprise-grade RAG system with A/B testing & RAGAS evaluation',
    url: 'https://github.com/cbratkovics/rag-pipeline',
    siteName: 'RAG Pipeline Demo',
    type: 'website',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryProvider>{children}</QueryProvider>
        <Analytics />
      </body>
    </html>
  )
}
