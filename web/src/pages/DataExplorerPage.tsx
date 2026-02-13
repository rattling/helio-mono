import { FormEvent, useEffect, useMemo, useState } from 'react'

import { apiClient } from '../api/client'
import {
  type ExplorerDecisionResponse,
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
  const [view, setView] = useState<'lookup' | 'timeline' | 'state' | 'decision'>(context.view)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lookupData, setLookupData] = useState<ExplorerLookupResponse | null>(null)
  const [timelineData, setTimelineData] = useState<ExplorerTimelineResponse | null>(null)
  const [stateData, setStateData] = useState<ExplorerStateResponse | null>(null)
  const [decisionData, setDecisionData] = useState<ExplorerDecisionResponse | null>(null)

  useEffect(() => {
    setEntityType(context.entity_type ?? 'task')
    setEntityId(context.entity_id ?? '')
    setView(context.view)
  }, [context.entity_id, context.entity_type, context.view])

  const activePayload = useMemo(() => {
    if (view === 'lookup') return lookupData
    if (view === 'timeline') return timelineData
    if (view === 'state') return stateData
    return decisionData
  }, [decisionData, lookupData, stateData, timelineData, view])

  async function runLookup() {
    setLoading(true)
    setError(null)
    try {
      const payload = await apiClient.getExplorerLookup(entityType, entityId)
      setLookupData(payload)
      onContextChange({ ...context, entity_type: entityType, entity_id: entityId, view: 'lookup' })
      setView('lookup')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function runTimeline() {
    setLoading(true)
    setError(null)
    try {
      const payload = await apiClient.getExplorerTimeline(entityType, entityId)
      setTimelineData(payload)
      onContextChange({ ...context, entity_type: entityType, entity_id: entityId, view: 'timeline' })
      setView('timeline')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function runState() {
    setLoading(true)
    setError(null)
    try {
      const payload = await apiClient.getExplorerState(entityType, entityId)
      setStateData(payload)
      onContextChange({ ...context, entity_type: entityType, entity_id: entityId, view: 'state' })
      setView('state')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function runDecision() {
    setLoading(true)
    setError(null)
    try {
      const payload = await apiClient.getExplorerDecision(entityType, entityId)
      setDecisionData(payload)
      onContextChange({ ...context, entity_type: entityType, entity_id: entityId, view: 'decision' })
      setView('decision')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void runLookup()
  }

  return (
    <div>
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
            <button className="ghost" type="button" onClick={() => void runTimeline()}>
              Timeline
            </button>
            <button className="ghost" type="button" onClick={() => void runState()}>
              State
            </button>
            <button className="ghost" type="button" onClick={() => void runDecision()}>
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
    </div>
  )
}
