import {
  ControlRoomOverview,
  ControlRoomOverviewSchema,
  Task,
  TaskIngestResult,
  TaskIngestResultSchema,
  TaskSchema,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type TaskListParams = {
  status?: string
  project?: string
  search?: string
  sort_by?: 'updated_at' | 'created_at' | 'due_at' | 'priority' | 'title' | 'status'
  sort_dir?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === '') continue
    query.set(key, String(value))
  }
  const text = query.toString()
  return text ? `?${text}` : ''
}

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(`API ${response.status}: ${message || 'request failed'}`)
  }

  return response.json()
}

export const apiClient = {
  async listTasks(params: TaskListParams = {}): Promise<Task[]> {
    const data = await request(`/api/v1/tasks${buildQuery(params as Record<string, string | number | undefined>)}`)
    return TaskSchema.array().parse(data)
  },

  async getTask(taskId: string): Promise<Task> {
    const data = await request(`/api/v1/tasks/${taskId}`)
    return TaskSchema.parse(data)
  },

  async ingestTask(payload: {
    title: string
    body?: string
    source_ref: string
    priority?: 'p0' | 'p1' | 'p2' | 'p3'
    project?: string
  }): Promise<TaskIngestResult> {
    const data = await request('/api/v1/tasks/ingest', {
      method: 'POST',
      body: JSON.stringify({
        source: 'api',
        ...payload,
      }),
    })
    return TaskIngestResultSchema.parse(data)
  },

  async patchTask(taskId: string, payload: Partial<Pick<Task, 'title' | 'body' | 'priority' | 'project' | 'status'>>): Promise<Task> {
    const data = await request(`/api/v1/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
    return TaskSchema.parse(data)
  },

  async completeTask(taskId: string): Promise<Task> {
    const data = await request(`/api/v1/tasks/${taskId}/complete`, {
      method: 'POST',
    })
    return TaskSchema.parse(data)
  },

  async snoozeTask(taskId: string, until: string, rationale?: string): Promise<Task> {
    const data = await request(`/api/v1/tasks/${taskId}/snooze`, {
      method: 'POST',
      body: JSON.stringify({ until, rationale }),
    })
    return TaskSchema.parse(data)
  },

  async getControlRoomOverview(): Promise<ControlRoomOverview> {
    const data = await request('/api/v1/control-room/overview')
    return ControlRoomOverviewSchema.parse(data)
  },
}
