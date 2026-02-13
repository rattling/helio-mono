import { FormEvent, useEffect, useMemo, useState } from 'react'

import { apiClient } from '../api/client'
import {
  type ExplorerDecisionResponse,
  type ExplorerGuidedInsightsResponse,
  type ExplorerLookupResponse,
  type ExplorerStateResponse,
  type ExplorerTimelineResponse,
} from '../api/types'
import { ExplorerDeepLinkContext } from '../explorerContext'

type Props = {
  context: ExplorerDeepLinkContext
  onContextChange: (next: ExplorerDeepLinkContext) => void
}

export function DataExplorerPage({ context, onContextChange }: Props) {
  const [entityType, setEntityType] = useState<'task' | 'event'>(context.entity_type ?? 'task')
  const [entityId, setEntityId] = useState(context.entity_id ?? '')
  const [mode, setMode] = useState<'guided' | 'ad_hoc'>(context.mode ?? 'guided')
  const [view, setView] = useState<'lookup' | 'timeline' | 'state' | 'decision'>(context.view)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [insights, setInsights] = useState<ExplorerGuidedInsightsResponse | null>(null)
  const [lookupData, setLookupData] = useState<ExplorerLookupResponse | null>(null)
  const [timelineData, setTimelineData] = useState<ExplorerTimelineResponse | null>(null)
  const [stateData, setStateData] = useState<ExplorerStateResponse | null>(null)
  const [decisionData, setDecisionData] = useState<ExplorerDecisionResponse | null>(null)

  useEffect(() => {
    setEntityType(context.entity_type ?? 'task')
    setEntityId(context.entity_id ?? '')
    setMode(context.mode ?? 'guided')
    setView(context.view)
  }, [context.entity_id, context.entity_type, context.mode, context.view])

  useEffect(() => {
    if (mode !== 'guided') return
    void loadInsights()
  }, [mode])

  const activePayload = useMemo(() => {
    if (view === 'lookup') return lookupData
    if (view === 'timeline') return timelineData
    if (view === 'state') return stateData
    return decisionData
  }, [decisionData, lookupData, stateData, timelineData, view])

  async function loadInsights() {
    setLoading(true)
    setError(null)
    try {
      const payload = await apiClient.getExplorerInsights()
      setInsights(payload)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function runQuery(
    nextView: 'lookup' | 'timeline' | 'state' | 'decision',
    nextEntityType = entityType,
    nextEntityId = entityId,
  ) {
    setLoading(true)
    setError(null)
    try {
      if (nextView === 'lookup') {
        const payload = await apiClient.getExplorerLookup(nextEntityType, nextEntityId)
        setLookupData(payload)
      }
      if (nextView === 'timeline') {
        const payload = await apiClient.getExplorerTimeline(nextEntityType, nextEntityId)
        setTimelineData(payload)
      }
      if (nextView === 'state') {
        const payload = await apiClient.getExplorerState(nextEntityType, nextEntityId)
        setStateData(payload)
      }
      if (nextView === 'decision') {
        const payload = await apiClient.getExplorerDecision(nextEntityType, nextEntityId)
        setDecisionData(payload)
      }
      onContextChange({
        ...context,
        entity_type: nextEntityType,
        entity_id: nextEntityId,
        mode: 'ad_hoc',
        view: nextView,
      })
      setEntityType(nextEntityType)
      setEntityId(nextEntityId)
      setMode('ad_hoc')
      setView(nextView)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function switchMode(nextMode: 'guided' | 'ad_hoc') {
    setMode(nextMode)
    onContextChange({ ...context, mode: nextMode, entity_type: entityType, entity_id: entityId, view })
  }

  async function drilldown(
    nextView: 'lookup' | 'timeline' | 'state' | 'decision',
    nextEntityType: 'task' | 'event',
    nextEntityId: string,
  ) {
    await runQuery(nextView, nextEntityType, nextEntityId)
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void runQuery('lookup')
  }

  return (
    <div>
      <section className="panel">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h3>Mode</h3>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className={mode === 'guided' ? 'primary' : 'ghost'}
              type="button"
              onClick={() => switchMode('guided')}
            >
              Guided Insights
            </button>
            <button
              className={mode === 'ad_hoc' ? 'primary' : 'ghost'}
              type="button"
              onClick={() => switchMode('ad_hoc')}
            >
              Ad Hoc Query
            </button>
          </div>
        </div>
      </section>

      {mode === 'guided' && (
        <>
          <section className="panel">
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <h3>System Pulse</h3>
              <button className="ghost" type="button" onClick={() => void loadInsights()}>
                Refresh
              </button>
            </div>
            {!insights && !loading && <p className="small">No insights loaded yet.</p>}
            {insights && (
              <div className="row">
                {insights.pulse.metrics.map((metric) => (
                  <div key={metric.key} className="panel" style={{ marginBottom: 0 }}>
                    <strong>{metric.label}</strong>
                    <div>{String(metric.value)}</div>
                    <div className="small">Status: {metric.status}</div>
                    {metric.description && <div className="small">{metric.description}</div>}
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <h3>Notable Events</h3>
            {!insights && !loading && <p className="small">No notable events yet.</p>}
            {insights?.notable_events.map((item) => (
              <div key={item.notable_id} className="panel" style={{ marginBottom: '0.5rem' }}>
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <strong>{item.title}</strong>
                  <span className="small">
                    {item.ranking.severity} · score {item.ranking.composite_score.toFixed(2)}
                  </span>
                </div>
                <div className="small">{item.summary}</div>
                <div className="small">{new Date(item.timestamp).toLocaleString()}</div>
                <div className="small">
                  Why ranked:{' '}
                  {item.ranking.factors
                    .map((factor) => `${factor.label} ${factor.value.toFixed(2)}`)
                    .join(' · ')}
                </div>
                <div className="row" style={{ marginTop: '0.5rem' }}>
                  {item.evidence_refs.slice(0, 2).map((ref, index) => (
                    <button
                      key={`${item.notable_id}-${index}`}
                      className="ghost"
                      type="button"
                      onClick={() => void drilldown(ref.view, ref.entity_type, ref.entity_id)}
                    >
                      Open {ref.view}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </section>
        </>
      )}

      {mode === 'ad_hoc' && (
        <>
      <section className="panel">
        <h3>Entity Lookup</h3>
        <form onSubmit={submitSearch}>
          <div className="row">
            <div className="field">
              <label htmlFor="explorer-entity-type">Entity Type</label>
              <select
                id="explorer-entity-type"
                value={entityType}
                onChange={(event) => setEntityType(event.target.value as 'task' | 'event')}
              >
                <option value="task">task</option>
                <option value="event">event</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="explorer-entity-id">Entity ID</label>
              <input
                id="explorer-entity-id"
                value={entityId}
                onChange={(event) => setEntityId(event.target.value)}
                placeholder="task uuid / event uuid"
                required
              />
            </div>
          </div>
          <div className="row">
            <button className="primary" type="submit">
              Lookup
            </button>
            <button className="ghost" type="button" onClick={() => void runQuery('timeline')}>
              Timeline
            </button>
            <button className="ghost" type="button" onClick={() => void runQuery('state')}>
              State
            </button>
            <button className="ghost" type="button" onClick={() => void runQuery('decision')}>
              Decision
            </button>
          </div>
        </form>
        {loading && <p className="small">Loading…</p>}
        {error && <p className="small">Error: {error}</p>}
      </section>

      <section className="panel">
        <h3>Interpreted View ({view})</h3>
        {!activePayload && <p className="small">Run a lookup/timeline/state/decision query.</p>}

        {view === 'lookup' && lookupData && (
          <dl className="kv">
            <dt>Entity</dt>
            <dd>
              {lookupData.entity_type}:{lookupData.entity_id}
            </dd>
            <dt>Related IDs</dt>
            <dd>{lookupData.related_identifiers.length}</dd>
          </dl>
        )}

        {view === 'timeline' && timelineData && (
          <div>
            <p className="small">Events: {timelineData.events.length}</p>
            {timelineData.events.slice(0, 20).map((event) => (
              <div key={event.event_id} className="panel" style={{ marginBottom: '0.5rem' }}>
                <strong>{event.event_type}</strong>
                <div className="small">{new Date(event.timestamp).toLocaleString()}</div>
                {event.rationale && <div className="small">{event.rationale}</div>}
              </div>
            ))}
          </div>
        )}

        {view === 'state' && stateData && (
          <dl className="kv">
            <dt>Entity</dt>
            <dd>{stateData.entity_id}</dd>
            <dt>Trace events</dt>
            <dd>{stateData.traceability.event_count ?? 0}</dd>
            <dt>Latest event</dt>
            <dd>{stateData.traceability.latest_event_id ?? 'n/a'}</dd>
          </dl>
        )}

        {view === 'decision' && decisionData && (
          <div>
            <p className="small">Decision-like events: {decisionData.decisions.length}</p>
            {decisionData.decisions.slice(0, 20).map((event) => (
              <div key={event.event_id} className="panel" style={{ marginBottom: '0.5rem' }}>
                <strong>{event.event_type}</strong>
                <div className="small">{event.rationale ?? 'no rationale'}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h3>Raw Payload</h3>
        <div className="code">{activePayload ? JSON.stringify(activePayload, null, 2) : 'No payload loaded.'}</div>
      </section>
        </>
      )}
    </div>
  )
}
