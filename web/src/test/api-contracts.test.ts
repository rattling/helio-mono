import { describe, expect, it, vi } from 'vitest'

import { apiClient } from '../api/client'
import {
  ControlRoomOverviewSchema,
  ExplorerLookupResponseSchema,
  ExplorerTimelineResponseSchema,
  TaskSchema,
} from '../api/types'

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

  it('accepts nullable readiness check fields', () => {
    const parsed = ControlRoomOverviewSchema.parse({
      health: { status: 'healthy', service: 'helionyx' },
      readiness: {
        status: 'ready',
        checks: {
          event_store: { path: '/tmp/events', accessible: true, parent_accessible: null },
          projections_db: {
            path: '/tmp/projections.db',
            accessible: null,
            parent_accessible: true,
          },
        },
      },
      attention_today: { top_actionable: [] },
      attention_week: { due_this_week: [] },
      generated_at: '2026-02-13T12:00:00',
    })

    expect(parsed.readiness.checks.event_store.parent_accessible).toBeNull()
    expect(parsed.readiness.checks.projections_db.accessible).toBeNull()
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

  it('parses explorer lookup response shape', () => {
    const parsed = ExplorerLookupResponseSchema.parse({
      entity_type: 'task',
      entity_id: 'task-1',
      canonical: { task_id: 'task-1' },
      related_identifiers: [
        {
          entity_type: 'task',
          entity_id: 'task-2',
          relation: 'blocked_by',
        },
      ],
    })
    expect(parsed.related_identifiers[0].relation).toBe('blocked_by')
  })

  it('parses explorer timeline response shape', () => {
    const parsed = ExplorerTimelineResponseSchema.parse({
      entity_type: 'task',
      entity_id: 'task-1',
      events: [
        {
          event_id: 'evt-1',
          event_type: 'decision_recorded',
          timestamp: '2026-02-13T12:00:00',
          links: [],
          payload: {},
        },
      ],
    })
    expect(parsed.events.length).toBe(1)
  })
})
