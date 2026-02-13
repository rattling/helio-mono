import { z } from 'zod'

export const TaskSchema = z.object({
  task_id: z.string(),
  title: z.string(),
  body: z.string().nullable().optional(),
  status: z.string(),
  priority: z.string(),
  due_at: z.string().nullable().optional(),
  do_not_start_before: z.string().nullable().optional(),
  updated_at: z.string(),
  project: z.string().nullable().optional(),
  labels: z.array(z.string()).default([]),
  blocked_by: z.array(z.string()).default([]),
  explanations: z.array(z.object({
    ts: z.string().optional(),
    actor: z.string().optional(),
    action: z.string().optional(),
    rationale: z.string().optional(),
  })).default([]),
})

export type Task = z.infer<typeof TaskSchema>

export const TaskIngestResultSchema = z.object({
  task_id: z.string(),
  created: z.boolean(),
  decision_rationale: z.string().nullable().optional(),
})

export type TaskIngestResult = z.infer<typeof TaskIngestResultSchema>

export const ControlRoomOverviewSchema = z.object({
  health: z.object({
    status: z.string(),
    service: z.string(),
  }),
  readiness: z.object({
    status: z.string(),
    checks: z.record(
      z.object({
        path: z.string(),
        accessible: z.boolean().nullable().optional(),
        parent_accessible: z.boolean().nullable().optional(),
      }),
    ),
  }),
  attention_today: z.object({
    top_actionable: z.array(z.record(z.any())).default([]),
  }).and(z.record(z.any())),
  attention_week: z.object({
    due_this_week: z.array(z.record(z.any())).default([]),
  }).and(z.record(z.any())),
  generated_at: z.string(),
})

export type ControlRoomOverview = z.infer<typeof ControlRoomOverviewSchema>

export const ExplorerIdentifierRefSchema = z.object({
  entity_type: z.enum(['task', 'event']),
  entity_id: z.string(),
  relation: z.string(),
})

export const ExplorerLookupResponseSchema = z.object({
  entity_type: z.enum(['task', 'event']),
  entity_id: z.string(),
  canonical: z.record(z.any()),
  related_identifiers: z.array(ExplorerIdentifierRefSchema).default([]),
})

export type ExplorerLookupResponse = z.infer<typeof ExplorerLookupResponseSchema>

export const ExplorerTimelineEventSchema = z.object({
  event_id: z.string(),
  event_type: z.string(),
  timestamp: z.string(),
  rationale: z.string().nullable().optional(),
  links: z.array(ExplorerIdentifierRefSchema).default([]),
  payload: z.record(z.any()),
})

export const ExplorerTimelineResponseSchema = z.object({
  entity_type: z.enum(['task', 'event']),
  entity_id: z.string(),
  events: z.array(ExplorerTimelineEventSchema).default([]),
  since: z.string().nullable().optional(),
  until: z.string().nullable().optional(),
})

export type ExplorerTimelineResponse = z.infer<typeof ExplorerTimelineResponseSchema>

export const ExplorerStateResponseSchema = z.object({
  entity_type: z.enum(['task', 'event']),
  entity_id: z.string(),
  snapshot: z.record(z.any()),
  traceability: z.record(z.any()).default({}),
})

export type ExplorerStateResponse = z.infer<typeof ExplorerStateResponseSchema>

export const ExplorerDecisionResponseSchema = z.object({
  entity_type: z.enum(['task', 'event']),
  entity_id: z.string(),
  decisions: z.array(ExplorerTimelineEventSchema).default([]),
})

export type ExplorerDecisionResponse = z.infer<typeof ExplorerDecisionResponseSchema>
