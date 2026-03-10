'use client'

import { useState } from 'react'
import { Check, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ChartOutput } from '@/components/chat/chart-output'
import { acceptProposal, rejectProposal } from '@/lib/backend-client'
import { useChatStore } from '@/lib/stores/chat-store'
import { useDashboardStore } from '@/lib/stores/dashboard-store'
import type { CardProposal, PlotlyFigure } from '@/lib/api-types'

interface CardProposalsProps {
  projectId: string
  chatId: string
  messageId: string
  proposals: CardProposal[]
}

export function CardProposals({ projectId, chatId, messageId, proposals }: CardProposalsProps) {
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const updateProposalStatus = useChatStore((s) => s.updateProposalStatus)
  const loadCards = useDashboardStore((s) => s.loadCards)

  const handleAccept = async (proposal: CardProposal) => {
    setLoading((prev) => ({ ...prev, [proposal.proposal_id]: true }))
    try {
      await acceptProposal(projectId, chatId, messageId, proposal.proposal_id)
      updateProposalStatus(messageId, proposal.proposal_id, 'accepted')
      await loadCards(projectId)
    } catch (err) {
      console.error('Failed to accept proposal:', err)
    } finally {
      setLoading((prev) => ({ ...prev, [proposal.proposal_id]: false }))
    }
  }

  const handleReject = async (proposal: CardProposal) => {
    setLoading((prev) => ({ ...prev, [proposal.proposal_id]: true }))
    try {
      await rejectProposal(projectId, chatId, messageId, proposal.proposal_id)
      updateProposalStatus(messageId, proposal.proposal_id, 'rejected')
    } catch (err) {
      console.error('Failed to reject proposal:', err)
    } finally {
      setLoading((prev) => ({ ...prev, [proposal.proposal_id]: false }))
    }
  }

  return (
    <div className="space-y-4">
      {proposals.map((proposal) => (
        <div
          key={proposal.proposal_id}
          className="rounded-xl border border-border/50 bg-card p-4 shadow-sm"
        >
          <h4 className="mb-3 text-sm font-medium text-foreground">
            {proposal.card_title}
          </h4>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">Current</p>
              {proposal.current_fig ? (
                <ChartOutput
                  figure={proposal.current_fig as unknown as PlotlyFigure}
                  sourceAction={false}
                />
              ) : (
                <div className="flex aspect-video items-center justify-center rounded-lg border border-dashed border-border/50 bg-secondary/20 text-xs text-muted-foreground">
                  No chart
                </div>
              )}
            </div>
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">Proposed</p>
              {proposal.proposed_fig ? (
                <ChartOutput
                  figure={proposal.proposed_fig as unknown as PlotlyFigure}
                  sourceAction={false}
                />
              ) : (
                <div className="flex aspect-video items-center justify-center rounded-lg border border-dashed border-border/50 bg-secondary/20 text-xs text-muted-foreground">
                  No chart
                </div>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-center justify-end gap-2">
            {proposal.status === 'pending' ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 gap-1.5 text-xs"
                  onClick={() => handleReject(proposal)}
                  disabled={!!loading[proposal.proposal_id]}
                >
                  <X className="h-3.5 w-3.5" />
                  Reject
                </Button>
                <Button
                  size="sm"
                  className="h-8 gap-1.5 text-xs"
                  onClick={() => handleAccept(proposal)}
                  disabled={!!loading[proposal.proposal_id]}
                >
                  <Check className="h-3.5 w-3.5" />
                  Accept
                </Button>
              </>
            ) : (
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  proposal.status === 'accepted'
                    ? 'bg-green-500/10 text-green-600'
                    : 'bg-red-500/10 text-red-600'
                }`}
              >
                {proposal.status === 'accepted' ? (
                  <><Check className="h-3 w-3" /> Applied</>
                ) : (
                  <><X className="h-3 w-3" /> Rejected</>
                )}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
