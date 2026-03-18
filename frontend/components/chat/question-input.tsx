'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Question } from '@/lib/api-types'

interface QuestionInputProps {
  questions: Question[]
  onSubmit?: (answers: Record<string, string>) => void
}

export function QuestionInput({ questions, onSubmit }: QuestionInputProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({})
  const [showOther, setShowOther] = useState<Record<number, boolean>>({})
  const [otherValues, setOtherValues] = useState<Record<number, string>>({})
  const submittedRef = useRef(false)

  const isResolved = questions.every((q) => q.selected_answer)
  const isInteractive = !!onSubmit && !isResolved

  // Auto-submit when all questions have a local answer
  useEffect(() => {
    if (
      !submittedRef.current &&
      onSubmit &&
      questions.length > 0 &&
      questions.every((q) => selectedAnswers[q.question])
    ) {
      submittedRef.current = true
      onSubmit(selectedAnswers)
    }
  }, [selectedAnswers, questions, onSubmit])

  const handleOptionClick = useCallback(
    (question: Question, label: string) => {
      if (submittedRef.current) return
      setSelectedAnswers((prev) => ({ ...prev, [question.question]: label }))
    },
    []
  )

  const handleOtherSubmit = useCallback(
    (questionIdx: number, question: Question) => {
      const value = otherValues[questionIdx]
      if (!value?.trim() || submittedRef.current) return
      setSelectedAnswers((prev) => ({ ...prev, [question.question]: value.trim() }))
    },
    [otherValues]
  )

  return (
    <div className="space-y-4 py-1">
      {questions.map((q, qi) => {
        const localAnswer = selectedAnswers[q.question]
        const resolvedAnswer = q.selected_answer
        const answered = !!localAnswer || !!resolvedAnswer

        return (
          <div key={qi} className="space-y-2">
            {q.header && (
              <p className="text-sm text-muted-foreground">{q.header}</p>
            )}
            <p className="text-sm font-medium">{q.question}</p>

            <div className="flex flex-wrap gap-1.5">
              {q.options.map((opt, oi) => {
                const isSelected = resolvedAnswer === opt.label || localAnswer === opt.label

                if (isInteractive && !localAnswer) {
                  return (
                    <Button
                      key={oi}
                      variant="outline"
                      size="sm"
                      onClick={() => handleOptionClick(q, opt.label)}
                      title={opt.description || undefined}
                      className="h-auto px-2 py-1 text-xs border-sky/30 bg-sky/5 hover:bg-sky/10 hover:border-sky/50"
                    >
                      {opt.label}
                    </Button>
                  )
                }

                return (
                  <span
                    key={oi}
                    className={`inline-flex rounded-md border px-2 py-1 text-xs ${
                      isSelected
                        ? 'border-primary bg-primary/10 text-primary font-medium'
                        : 'border-border/50 text-muted-foreground'
                    }`}
                  >
                    {opt.label}
                  </span>
                )
              })}
              {isInteractive && !localAnswer && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowOther((prev) => ({ ...prev, [qi]: true }))}
                  className="h-auto px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
                >
                  Other
                </Button>
              )}
            </div>

            {/* Free-text answer that doesn't match any option */}
            {(resolvedAnswer || localAnswer) && !q.options.some((o) => o.label === (resolvedAnswer || localAnswer)) && (
              <p className="text-xs text-primary italic">&rarr; {resolvedAnswer || localAnswer}</p>
            )}

            {isInteractive && !localAnswer && showOther[qi] && (
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
        )
      })}
    </div>
  )
}
