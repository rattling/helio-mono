import { FormEvent, useEffect, useMemo, useState } from 'react'

import { apiClient } from '../api/client'
import type { Task } from '../api/types'

const defaultForm = {
  title: '',
  body: '',
  project: '',
  priority: 'p2' as 'p0' | 'p1' | 'p2' | 'p3',
}

export function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('')
  const [form, setForm] = useState(defaultForm)
  const [refreshToken, setRefreshToken] = useState(0)

  useEffect(() => {
    let canceled = false
    setLoading(true)
    setError(null)

    apiClient
      .listTasks({
        search: query || undefined,
        status: status || undefined,
        sort_by: 'updated_at',
        sort_dir: 'desc',
        limit: 100,
      })
      .then((result) => {
        if (!canceled) {
          setTasks(result)
          if (!selectedTaskId && result.length > 0) {
            setSelectedTaskId(result[0].task_id)
          }
        }
      })
      .catch((err: Error) => {
        if (!canceled) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (!canceled) {
          setLoading(false)
        }
      })

    return () => {
      canceled = true
    }
  }, [query, refreshToken, selectedTaskId, status])

  const selectedTask = useMemo(
    () => tasks.find((task) => task.task_id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
  )

  async function onCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setError(null)
      const sourceRef = `ui-${Date.now()}`
      const result = await apiClient.ingestTask({
        title: form.title,
        body: form.body || undefined,
        source_ref: sourceRef,
        priority: form.priority,
        project: form.project || undefined,
      })
      setForm(defaultForm)
      setSelectedTaskId(result.task_id)
      setRefreshToken((value) => value + 1)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function onUpdateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedTask) return
    try {
      setError(null)
      await apiClient.patchTask(selectedTask.task_id, {
        title: selectedTask.title,
        body: selectedTask.body ?? undefined,
        priority: selectedTask.priority as 'p0' | 'p1' | 'p2' | 'p3',
        project: selectedTask.project ?? undefined,
      })
      setRefreshToken((value) => value + 1)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function completeTask() {
    if (!selectedTask) return
    try {
      setError(null)
      await apiClient.completeTask(selectedTask.task_id)
      setRefreshToken((value) => value + 1)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function snoozeTask() {
    if (!selectedTask) return
    try {
      setError(null)
      const tomorrow = new Date(Date.now() + 24 * 3600 * 1000).toISOString()
      await apiClient.snoozeTask(selectedTask.task_id, tomorrow, 'Snoozed from UI')
      setRefreshToken((value) => value + 1)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="row">
      <section className="panel">
        <h3>Create Task</h3>
        <form onSubmit={onCreateTask}>
          <div className="field">
            <label htmlFor="new-title">Title</label>
            <input
              id="new-title"
              required
              value={form.title}
              onChange={(event) => setForm((value) => ({ ...value, title: event.target.value }))}
            />
          </div>
          <div className="field">
            <label htmlFor="new-body">Body</label>
            <textarea
              id="new-body"
              rows={3}
              value={form.body}
              onChange={(event) => setForm((value) => ({ ...value, body: event.target.value }))}
            />
          </div>
          <div className="field">
            <label htmlFor="new-project">Project</label>
            <input
              id="new-project"
              value={form.project}
              onChange={(event) =>
                setForm((value) => ({ ...value, project: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label htmlFor="new-priority">Priority</label>
            <select
              id="new-priority"
              value={form.priority}
              onChange={(event) =>
                setForm((value) => ({ ...value, priority: event.target.value as 'p0' | 'p1' | 'p2' | 'p3' }))
              }
            >
              <option value="p0">p0</option>
              <option value="p1">p1</option>
              <option value="p2">p2</option>
              <option value="p3">p3</option>
            </select>
          </div>
          <button className="primary" type="submit">
            Add task
          </button>
        </form>
      </section>

      <section className="panel">
        <h3>Task List</h3>
        <div className="row">
          <div className="field">
            <label htmlFor="task-search">Search</label>
            <input id="task-search" value={query} onChange={(event) => setQuery(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="task-status">Status</label>
            <select id="task-status" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">all</option>
              <option value="open">open</option>
              <option value="in_progress">in_progress</option>
              <option value="blocked">blocked</option>
              <option value="snoozed">snoozed</option>
              <option value="done">done</option>
            </select>
          </div>
        </div>

        {loading && <p className="small">Loading tasks…</p>}
        {error && <p className="small">Error: {error}</p>}

        <table className="table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Priority</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.task_id} onClick={() => setSelectedTaskId(task.task_id)}>
                <td>{task.title}</td>
                <td>{task.status}</td>
                <td>{task.priority}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h3>Task Detail</h3>
        {!selectedTask && <p className="small">Select a task to inspect and edit.</p>}

        {selectedTask && (
          <form onSubmit={onUpdateTask}>
            <div className="field">
              <label htmlFor="edit-title">Title</label>
              <input
                id="edit-title"
                value={selectedTask.title}
                onChange={(event) => {
                  const value = event.target.value
                  setTasks((existing) =>
                    existing.map((task) =>
                      task.task_id === selectedTask.task_id ? { ...task, title: value } : task,
                    ),
                  )
                }}
              />
            </div>
            <div className="field">
              <label htmlFor="edit-body">Body</label>
              <textarea
                id="edit-body"
                rows={4}
                value={selectedTask.body ?? ''}
                onChange={(event) => {
                  const value = event.target.value
                  setTasks((existing) =>
                    existing.map((task) =>
                      task.task_id === selectedTask.task_id ? { ...task, body: value } : task,
                    ),
                  )
                }}
              />
            </div>
            <div className="field">
              <label htmlFor="edit-priority">Priority</label>
              <select
                id="edit-priority"
                value={selectedTask.priority}
                onChange={(event) => {
                  const value = event.target.value
                  setTasks((existing) =>
                    existing.map((task) =>
                      task.task_id === selectedTask.task_id ? { ...task, priority: value } : task,
                    ),
                  )
                }}
              >
                <option value="p0">p0</option>
                <option value="p1">p1</option>
                <option value="p2">p2</option>
                <option value="p3">p3</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="edit-project">Project</label>
              <input
                id="edit-project"
                value={selectedTask.project ?? ''}
                onChange={(event) => {
                  const value = event.target.value
                  setTasks((existing) =>
                    existing.map((task) =>
                      task.task_id === selectedTask.task_id ? { ...task, project: value } : task,
                    ),
                  )
                }}
              />
            </div>

            <div className="row">
              <button className="primary" type="submit">
                Save edits
              </button>
              <button className="ghost" type="button" onClick={completeTask}>
                Mark done
              </button>
              <button className="ghost" type="button" onClick={snoozeTask}>
                Snooze 24h
              </button>
            </div>

            <p className="small">Task ID: {selectedTask.task_id}</p>
          </form>
        )}
      </section>
    </div>
  )
}
