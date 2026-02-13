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
