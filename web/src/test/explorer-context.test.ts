import { describe, expect, it } from 'vitest'

import { applyExplorerContext, parseExplorerContext } from '../explorerContext'

describe('explorer deep link context', () => {
  it('parses context from query params', () => {
    const context = parseExplorerContext('?explorer_entity_type=task&explorer_entity_id=abc&explorer_view=timeline')
    expect(context.entity_type).toBe('task')
    expect(context.entity_id).toBe('abc')
    expect(context.view).toBe('timeline')
  })

  it('round-trips context into query params', () => {
    const query = applyExplorerContext('', {
      entity_type: 'event',
      entity_id: 'uuid-1',
      view: 'decision',
    })
    const parsed = parseExplorerContext(`?${query}`)
    expect(parsed.entity_type).toBe('event')
    expect(parsed.entity_id).toBe('uuid-1')
    expect(parsed.view).toBe('decision')
  })
})
