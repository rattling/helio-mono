import { z } from 'zod'

export const ExplorerEntityTypeSchema = z.enum(['task', 'event'])
export const ExplorerViewSchema = z.enum(['lookup', 'timeline', 'state', 'decision'])
export const ExplorerModeSchema = z.enum(['guided', 'ad_hoc'])

export const ExplorerDeepLinkContextSchema = z.object({
  entity_type: ExplorerEntityTypeSchema.optional(),
  entity_id: z.string().optional(),
  view: ExplorerViewSchema.default('lookup'),
  mode: ExplorerModeSchema.default('guided'),
  since: z.string().optional(),
  until: z.string().optional(),
})

export type ExplorerDeepLinkContext = z.infer<typeof ExplorerDeepLinkContextSchema>

export function parseExplorerContext(search: string): ExplorerDeepLinkContext {
  const params = new URLSearchParams(search)
  return ExplorerDeepLinkContextSchema.parse({
    entity_type: params.get('explorer_entity_type') ?? undefined,
    entity_id: params.get('explorer_entity_id') ?? undefined,
    view: params.get('explorer_view') ?? undefined,
    mode: params.get('explorer_mode') ?? undefined,
    since: params.get('explorer_since') ?? undefined,
    until: params.get('explorer_until') ?? undefined,
  })
}

export function applyExplorerContext(search: string, context: ExplorerDeepLinkContext): string {
  const params = new URLSearchParams(search)

  if (context.entity_type) params.set('explorer_entity_type', context.entity_type)
  else params.delete('explorer_entity_type')

  if (context.entity_id) params.set('explorer_entity_id', context.entity_id)
  else params.delete('explorer_entity_id')

  if (context.view) params.set('explorer_view', context.view)
  else params.delete('explorer_view')

  if (context.mode) params.set('explorer_mode', context.mode)
  else params.delete('explorer_mode')

  if (context.since) params.set('explorer_since', context.since)
  else params.delete('explorer_since')

  if (context.until) params.set('explorer_until', context.until)
  else params.delete('explorer_until')

  return params.toString()
}
