'use client'

import { useCallback, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Question } from '@/lib/api-types'

interface QuestionInputProps {
  questions: Question[]
  onSubmit: (answers: Record<string, string>) => void
}

export function QuestionInput({ questions, onSubmit }: QuestionInputProps) {
  const [showOther, setShowOther] = useState<Record<number, boolean>>({})
  const [otherValues, setOtherValues] = useState<Record<number, string>>({})

  const handleOptionClick = useCallback(
    (questionIdx: number, question: Question, label: string) => {
      // for now, single question at a time
      onSubmit({ [question.question]: label })
    },
    [onSubmit]
  )

  const handleOtherSubmit = useCallback(
    (questionIdx: number, question: Question) => {
      const value = otherValues[questionIdx]
      if (!value?.trim()) return
      onSubmit({ [question.question]: value.trim() })
    },
    [onSubmit, otherValues]
  )

  return (
    <div className="space-y-6">
      {questions.map((q, qi) => (
        <div key={qi} className="space-y-3">
          {q.header && (
            <p className="text-sm text-muted-foreground">{q.header}</p>
          )}
          <p className="font-medium">{q.question}</p>

          <div className="flex flex-wrap gap-2">
            {q.options.map((opt, oi) => (
              <Button
                key={oi}
                variant="outline"
                size="sm"
                onClick={() => handleOptionClick(qi, q, opt.label)}
                title={opt.description || undefined}
                className="border-sky/30 bg-sky/5 hover:bg-sky/10 hover:border-sky/50"
              >
                {opt.label}
              </Button>
            ))}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowOther((prev) => ({ ...prev, [qi]: true }))}
              className="text-muted-foreground hover:text-foreground"
            >
              Other
            </Button>
          </div>

          {showOther[qi] && (
            <div className="flex gap-2">
              <Input
                placeholder="Your answer..."
                value={otherValues[qi] || ''}
                onChange={(e) =>
                  setOtherValues((prev) => ({ ...prev, [qi]: e.target.value }))
                }
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleOtherSubmit(qi, q)
                  }
                }}
              />
              <Button
                size="sm"
                onClick={() => handleOtherSubmit(qi, q)}
                disabled={!otherValues[qi]?.trim()}
              >
                Submit
              </Button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
