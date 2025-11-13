'use client'

import { useState } from 'react'
import { Card, CardContent } from './ui/card'
import { Button } from './ui/button'
import { ChevronRight, PlayCircle, Sparkles, X } from 'lucide-react'

interface DemoStep {
  id: string
  title: string
  query: string
  description: string
  highlight: string
}

interface GuidedDemoProps {
  onQuerySubmit: (query: string) => void
  isQueryLoading: boolean
}

const demoSteps: DemoStep[] = [
  {
    id: 'hybrid-search',
    title: 'Experience Hybrid Search',
    query: 'What is the difference between BM25 and vector search in RAG?',
    description: 'See how our system combines keyword and semantic search for superior results.',
    highlight: 'Watch the dual scoring system in action',
  },
  {
    id: 'cache-performance',
    title: 'Witness Cache Acceleration',
    query: 'How does caching improve RAG performance?',
    description: 'Submit this query twice to see dramatic latency reduction.',
    highlight: 'Second query will be 95% faster',
  },
  {
    id: 'ragas-evaluation',
    title: 'Real-time Quality Assessment',
    query: 'Explain RAGAS evaluation metrics with examples',
    description: 'Observe how we measure answer quality in real-time.',
    highlight: 'Four quality dimensions evaluated instantly',
  },
  {
    id: 'cost-optimization',
    title: 'Cost-Efficient Architecture',
    query: 'What strategies reduce costs in production RAG systems?',
    description: 'Learn how we achieve 83% cost reduction.',
    highlight: 'Multiple optimization layers working together',
  },
]

export function GuidedDemo({ onQuerySubmit, isQueryLoading }: GuidedDemoProps) {
  const [isActive, setIsActive] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  const handleStepClick = (index: number) => {
    setCurrentStep(index)
    const step = demoSteps[index]
    onQuerySubmit(step.query)
  }

  const handleNext = () => {
    if (currentStep < demoSteps.length - 1) {
      handleStepClick(currentStep + 1)
    }
  }

  if (!isActive) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={() => setIsActive(true)}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg h-auto py-3 px-5"
          size="lg"
        >
          <PlayCircle className="mr-2 h-5 w-5" />
          <span className="font-semibold">Start Guided Demo</span>
        </Button>
      </div>
    )
  }

  return (
    <div className="fixed right-6 top-24 w-96 z-50 animate-in slide-in-from-right">
      <Card className="shadow-2xl border-2 border-purple-200">
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              <span className="font-semibold">Interactive Demo</span>
            </div>
            <button
              onClick={() => setIsActive(false)}
              className="text-white/80 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="text-sm text-white/80 mt-1">
            Step {currentStep + 1} of {demoSteps.length}
          </div>
        </div>

        <CardContent className="p-5 space-y-4">
          <div>
            <h3 className="font-semibold text-base text-gray-900">
              {demoSteps[currentStep].title}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {demoSteps[currentStep].description}
            </p>
          </div>

          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="text-xs font-semibold text-blue-900 mb-1.5">
              Query to Try:
            </div>
            <div className="text-sm text-blue-800 font-mono bg-white p-2.5 rounded border border-blue-200 leading-snug">
              {demoSteps[currentStep].query}
            </div>
          </div>

          <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
            <div className="text-xs font-semibold text-amber-900 mb-1">
              What to Watch:
            </div>
            <div className="text-sm text-amber-800">
              {demoSteps[currentStep].highlight}
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              onClick={() => handleStepClick(currentStep)}
              disabled={isQueryLoading}
              className="flex-1 bg-purple-600 hover:bg-purple-700"
              size="sm"
            >
              {isQueryLoading ? 'Running...' : 'Run This Query'}
            </Button>

            {currentStep < demoSteps.length - 1 && (
              <Button
                onClick={handleNext}
                disabled={isQueryLoading}
                variant="outline"
                size="sm"
                className="px-3"
              >
                Next
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            )}
          </div>

          <div className="flex gap-1.5 justify-center pt-1">
            {demoSteps.map((_, index) => (
              <div
                key={index}
                className={`h-1.5 rounded-full transition-all ${
                  index === currentStep
                    ? 'w-8 bg-purple-600'
                    : index < currentStep
                    ? 'w-1.5 bg-green-500'
                    : 'w-1.5 bg-gray-300'
                }`}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
