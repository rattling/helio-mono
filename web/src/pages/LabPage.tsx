import { FormEvent, useEffect, useState } from 'react'

import { apiClient } from '../api/client'
import type {
  LabControlUpdateResponse,
  LabExperimentHistory,
  LabExperimentRunResult,
  LabOverview,
} from '../api/types'

export function LabPage() {
  const [overview, setOverview] = useState<LabOverview | null>(null)
  const [history, setHistory] = useState<LabExperimentHistory | null>(null)
  const [lastRun, setLastRun] = useState<LabExperimentRunResult | null>(null)
  const [lastControlResult, setLastControlResult] = useState<LabControlUpdateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [actor, setActor] = useState('operator')
  const [rationale, setRationale] = useState('')
  const [mode, setMode] = useState<'deterministic' | 'shadow' | 'bounded'>('deterministic')
  const [threshold, setThreshold] = useState('0.6')

  const [experimentMode, setExperimentMode] = useState<'deterministic' | 'shadow' | 'bounded'>('shadow')
  const [experimentThreshold, setExperimentThreshold] = useState('0.6')
  const [experimentRationale, setExperimentRationale] = useState('')

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [overviewPayload, historyPayload] = await Promise.all([
        apiClient.getLabOverview(),
        apiClient.getLabExperimentHistory(),
      ])
      setOverview(overviewPayload)
      setHistory(historyPayload)
      setMode(overviewPayload.config.mode)
      setThreshold(String(overviewPayload.config.shadow_confidence_threshold))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function submitControls(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.updateLabControls({
        actor,
        rationale,
        mode,
        shadow_confidence_threshold: Number(threshold),
      })
      setLastControlResult(result)
      setRationale('')
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function rollbackControls() {
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.rollbackLabControls({
        actor,
        rationale: rationale || 'operator rollback to deterministic baseline',
      })
      setLastControlResult(result)
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function submitExperiment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.runLabExperiment({
        actor,
        rationale: experimentRationale,
        candidate_mode: experimentMode,
        candidate_shadow_confidence_threshold: Number(experimentThreshold),
      })
      setLastRun(result)
      setExperimentRationale('')
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function applyRun(runId: string, action: 'apply' | 'rollback' | 'no_op') {
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.applyLabExperiment(runId, {
        actor,
        rationale: `experiment ${action}`,
        action,
      })
      setLastControlResult(result)
      await load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <section className="panel">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h3>Lab Overview</h3>
          <button className="ghost" onClick={() => void load()}>
            Refresh
          </button>
        </div>
        {loading && <p className="small">Loading lab data…</p>}
        {error && <p className="small">Error: {error}</p>}
        {overview && (
          <dl className="kv">
            <dt>Mode</dt>
            <dd>{overview.config.mode}</dd>
            <dt>Shadow enabled</dt>
            <dd>{String(overview.config.shadow_ranker_enabled)}</dd>
            <dt>Bounded enabled</dt>
            <dd>{String(overview.config.bounded_personalization_enabled)}</dd>
            <dt>Confidence threshold</dt>
            <dd>{overview.config.shadow_confidence_threshold}</dd>
          </dl>
        )}
      </section>

      <section className="panel">
        <h3>Learning Diagnostics</h3>
        {!overview && <p className="small">No diagnostics yet.</p>}
        {overview?.diagnostics.metrics.map((metric) => (
          <div key={metric.key} className="panel" style={{ marginBottom: '0.5rem' }}>
            <strong>{metric.label}</strong>
            <div>{String(metric.value)}</div>
            <div className="small">Status: {metric.status}</div>
            {metric.description && <div className="small">{metric.description}</div>}
          </div>
        ))}
      </section>

      <section className="panel">
        <h3>Bounded Controls</h3>
        <form onSubmit={submitControls}>
          <div className="row">
            <div className="field">
              <label htmlFor="lab-actor">Actor</label>
              <input id="lab-actor" value={actor} onChange={(e) => setActor(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="lab-mode">Mode</label>
              <select id="lab-mode" value={mode} onChange={(e) => setMode(e.target.value as 'deterministic' | 'shadow' | 'bounded')}>
                <option value="deterministic">deterministic</option>
                <option value="shadow">shadow</option>
                <option value="bounded">bounded</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="lab-threshold">Shadow Confidence Threshold</label>
              <input
                id="lab-threshold"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="field">
            <label htmlFor="lab-rationale">Rationale</label>
            <textarea id="lab-rationale" value={rationale} onChange={(e) => setRationale(e.target.value)} required />
          </div>
          <div className="row">
            <button className="primary" type="submit">Apply Controls</button>
            <button className="ghost" type="button" onClick={() => void rollbackControls()}>
              Rollback to Deterministic
            </button>
          </div>
        </form>
        {lastControlResult && (
          <p className="small">
            Last control update: {lastControlResult.status} (mode={lastControlResult.effective_config.mode})
          </p>
        )}
      </section>

      <section className="panel">
        <h3>Experiments</h3>
        <form onSubmit={submitExperiment}>
          <div className="row">
            <div className="field">
              <label htmlFor="exp-mode">Candidate Mode</label>
              <select id="exp-mode" value={experimentMode} onChange={(e) => setExperimentMode(e.target.value as 'deterministic' | 'shadow' | 'bounded')}>
                <option value="deterministic">deterministic</option>
                <option value="shadow">shadow</option>
                <option value="bounded">bounded</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="exp-threshold">Candidate Threshold</label>
              <input
                id="exp-threshold"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={experimentThreshold}
                onChange={(e) => setExperimentThreshold(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="field">
            <label htmlFor="exp-rationale">Experiment Rationale</label>
            <textarea id="exp-rationale" value={experimentRationale} onChange={(e) => setExperimentRationale(e.target.value)} required />
          </div>
          <button className="primary" type="submit">Run Experiment</button>
        </form>

        {lastRun && (
          <div className="code" style={{ marginTop: '0.75rem' }}>
            {JSON.stringify(lastRun, null, 2)}
          </div>
        )}
      </section>

      <section className="panel">
        <h3>Experiment History</h3>
        {!history?.runs.length && <p className="small">No runs yet.</p>}
        {history?.runs.map((run) => (
          <div key={run.run_id} className="panel" style={{ marginBottom: '0.5rem' }}>
            <strong>{run.run_id}</strong>
            <div className="small">
              {run.experiment_type} · {new Date(run.generated_at).toLocaleString()} · apply_allowed={String(run.apply_allowed)}
            </div>
            <div className="row" style={{ marginTop: '0.5rem' }}>
              <button className="ghost" type="button" onClick={() => void applyRun(run.run_id, 'apply')}>Apply</button>
              <button className="ghost" type="button" onClick={() => void applyRun(run.run_id, 'rollback')}>Rollback</button>
              <button className="ghost" type="button" onClick={() => void applyRun(run.run_id, 'no_op')}>No-op</button>
            </div>
          </div>
        ))}
      </section>
    </div>
  )
}
