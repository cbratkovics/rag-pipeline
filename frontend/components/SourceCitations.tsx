'use client'

import type { QueryResponse } from '@/types'

interface SourceCitationsProps {
  result: QueryResponse
}

export function SourceCitations({ result }: SourceCitationsProps) {
  return (
    <div>
      <h3>Source Citations</h3>
      {result.contexts?.map((context, idx) => (
        <div key={idx} className="mb-2">
          <p className="text-sm">{context}</p>
        </div>
      ))}
    </div>
  )
}
