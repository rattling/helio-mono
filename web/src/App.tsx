import { useMemo, useState } from 'react'

import { ControlRoomPage } from './pages/ControlRoomPage'
import { TasksPage } from './pages/TasksPage'

export type TopNavTab = 'tasks' | 'control-room'

export function App() {
  const [tab, setTab] = useState<TopNavTab>('tasks')

  const title = useMemo(() => {
    return tab === 'tasks' ? 'Tasks' : 'Control Room'
  }, [tab])

  return (
    <div className="app-shell">
      <header className="top-header">
        <h1>Helionyx UI</h1>
        <nav className="nav-tabs" aria-label="Primary">
          <button className={tab === 'tasks' ? 'active' : ''} onClick={() => setTab('tasks')}>
            Tasks
          </button>
          <button
            className={tab === 'control-room' ? 'active' : ''}
            onClick={() => setTab('control-room')}
          >
            Control Room
          </button>
        </nav>
      </header>

      <main className="page-content">
        <h2>{title}</h2>
        {tab === 'tasks' ? <TasksPage /> : <ControlRoomPage />}
      </main>
    </div>
  )
}
