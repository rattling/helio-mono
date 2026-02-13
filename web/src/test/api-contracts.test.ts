import { describe, expect, it, vi } from 'vitest'

import { apiClient } from '../api/client'
import { ControlRoomOverviewSchema, TaskSchema } from '../api/types'

describe('api contract alignment', () => {
  it('parses task payload shape', () => {
    const parsed = TaskSchema.parse({
      task_id: '11111111-1111-1111-1111-111111111111',
      title: 'Task title',
      body: 'Task body',
      status: 'open',
      priority: 'p2',
      updated_at: '2026-02-13T12:00:00',
      labels: [],
      blocked_by: [],
      explanations: [],
    })

    expect(parsed.title).toBe('Task title')
  })

  it('parses control room overview shape', () => {
    const parsed = ControlRoomOverviewSchema.parse({
      health: { status: 'healthy', service: 'helionyx' },
      readiness: {
        status: 'ready',
        checks: {
          event_store: { path: '/tmp/events', accessible: true },
          projections_db: { path: '/tmp/projections.db', parent_accessible: true },
        },
      },
      attention_today: { top_actionable: [] },
      attention_week: { due_this_week: [] },
      generated_at: '2026-02-13T12:00:00',
    })

    expect(parsed.readiness.status).toBe('ready')
  })

  it('fails fast on malformed task API response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => [{ title: 'missing task id' }],
      })),
    )

    await expect(apiClient.listTasks()).rejects.toThrow()
  })
})
