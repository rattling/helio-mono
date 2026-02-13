import { useEffect, useState } from 'react'

import { apiClient } from '../api/client'
import type { ControlRoomOverview } from '../api/types'

export function ControlRoomPage() {
  const [data, setData] = useState<ControlRoomOverview | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const payload = await apiClient.getControlRoomOverview()
      setData(payload)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div>
      <section className="panel">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h3>System Status</h3>
          <button className="ghost" onClick={() => void load()}>
            Refresh
          </button>
        </div>
        {loading && <p className="small">Loading control room data…</p>}
        {error && <p className="small">Error: {error}</p>}
        {data && (
          <dl className="kv">
            <dt>Health</dt>
            <dd>{data.health.status}</dd>
            <dt>Readiness</dt>
            <dd>{data.readiness.status}</dd>
            <dt>Generated</dt>
            <dd>{new Date(data.generated_at).toLocaleString()}</dd>
          </dl>
        )}
      </section>

      <section className="panel">
        <h3>Readiness Checks</h3>
        {!data && <p className="small">No data yet.</p>}
        {data && (
          <table className="table">
            <thead>
              <tr>
                <th>Dependency</th>
                <th>Path</th>
                <th>Accessible</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.readiness.checks).map(([name, check]) => (
                <tr key={name}>
                  <td>{name}</td>
                  <td>{check.path}</td>
                  <td>
                    {check.accessible !== undefined
                      ? String(check.accessible)
                      : String(check.parent_accessible)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <h3>Attention Today</h3>
        {!data && <p className="small">No data yet.</p>}
        {data && (
          <div>
            <p className="small">Top actionable: {data.attention_today.top_actionable.length}</p>
            {data.attention_today.top_actionable.slice(0, 5).map((item, index) => (
              <div key={`${item.task_id}-${index}`} className="panel" style={{ marginBottom: '0.5rem' }}>
                <strong>{item.task_id}</strong>
                <div className="small">{item.ranking_explanation ?? item.urgency_explanation}</div>
                <div className="code">
                  personalization_applied: {String(item.personalization_applied)}
                  {'\n'}policy: {item.personalization_policy ?? 'n/a'}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h3>Attention Week</h3>
        {!data && <p className="small">No data yet.</p>}
        {data && (
          <dl className="kv">
            <dt>Due this week</dt>
            <dd>{data.attention_week.due_this_week?.length ?? 0}</dd>
            <dt>High priority without due</dt>
            <dd>{data.attention_week.high_priority_without_due?.length ?? 0}</dd>
            <dt>Blocked summary</dt>
            <dd>{data.attention_week.blocked_summary?.length ?? 0}</dd>
          </dl>
        )}
      </section>
    </div>
  )
}
