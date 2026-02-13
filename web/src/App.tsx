import { useMemo, useState } from 'react'

import { ControlRoomPage } from './pages/ControlRoomPage'
import { DataExplorerPage } from './pages/DataExplorerPage'
import { LabPage } from './pages/LabPage'
import { TasksPage } from './pages/TasksPage'
import {
  ExplorerDeepLinkContext,
  applyExplorerContext,
  parseExplorerContext,
} from './explorerContext'

export type TopNavTab = 'tasks' | 'control-room' | 'data-explorer' | 'lab'

function parseInitialTab(): TopNavTab {
  const params = new URLSearchParams(window.location.search)
  const raw = params.get('tab')
  if (raw === 'tasks' || raw === 'control-room' || raw === 'data-explorer' || raw === 'lab') {
    return raw
  }
  return 'tasks'
}

export function App() {
  const [tab, setTab] = useState<TopNavTab>(parseInitialTab)
  const [explorerContext, setExplorerContext] = useState<ExplorerDeepLinkContext>(() =>
    parseExplorerContext(window.location.search),
  )

  const title = useMemo(() => {
    if (tab === 'tasks') return 'Tasks'
    if (tab === 'control-room') return 'Control Room'
    if (tab === 'lab') return 'Lab'
    return 'Data Explorer'
  }, [tab])

  function updateUrl(nextTab: TopNavTab, nextContext: ExplorerDeepLinkContext) {
    const params = new URLSearchParams(window.location.search)
    params.set('tab', nextTab)
    const explorerQuery = applyExplorerContext(params.toString(), nextContext)
    window.history.replaceState({}, '', `${window.location.pathname}?${explorerQuery}`)
  }

  function setActiveTab(next: TopNavTab) {
    setTab(next)
    updateUrl(next, explorerContext)
  }

  function onExplorerContextChange(next: ExplorerDeepLinkContext) {
    setExplorerContext(next)
    updateUrl(tab, next)
  }

  function openExplorerForTask(taskId: string) {
    const nextContext: ExplorerDeepLinkContext = {
      entity_type: 'task',
      entity_id: taskId,
      mode: 'ad_hoc',
      view: 'lookup',
    }
    setExplorerContext(nextContext)
    setTab('data-explorer')
    updateUrl('data-explorer', nextContext)
  }

  return (
    <div className="app-shell">
      <header className="top-header">
        <h1>Helionyx UI</h1>
        <nav className="nav-tabs" aria-label="Primary">
          <button className={tab === 'tasks' ? 'active' : ''} onClick={() => setActiveTab('tasks')}>
            Tasks
          </button>
          <button
            className={tab === 'control-room' ? 'active' : ''}
            onClick={() => setActiveTab('control-room')}
          >
            Control Room
          </button>
          <button
            className={tab === 'data-explorer' ? 'active' : ''}
            onClick={() => setActiveTab('data-explorer')}
          >
            Data Explorer
          </button>
          <button className={tab === 'lab' ? 'active' : ''} onClick={() => setActiveTab('lab')}>
            Lab
          </button>
        </nav>
      </header>

      <main className="page-content">
        <h2>{title}</h2>
        {tab === 'tasks' && <TasksPage />}
        {tab === 'control-room' && <ControlRoomPage onOpenExplorerTask={openExplorerForTask} />}
        {tab === 'data-explorer' && (
          <DataExplorerPage context={explorerContext} onContextChange={onExplorerContextChange} />
        )}
        {tab === 'lab' && <LabPage />}
      </main>
    </div>
  )
}
