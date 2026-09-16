export interface SseEvent {
  type: string
  [key: string]: unknown
}

export interface ParsedSseChunk {
  events: SseEvent[]
  rest: string
}

export function parseSseChunk(buffer: string): ParsedSseChunk {
  const normalized = buffer.replace(/\r\n/g, '\n')
  const frames = normalized.split('\n\n')
  const rest = frames.pop() ?? ''
  const events: SseEvent[] = []

  for (const frame of frames) {
    const data = frame
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
      .join('\n')
    if (!data) continue

    const event: unknown = JSON.parse(data)
    if (
      typeof event !== 'object' ||
      event === null ||
      typeof (event as { type?: unknown }).type !== 'string'
    ) {
      throw new Error('Invalid SSE event payload')
    }
    events.push(event as SseEvent)
  }

  return { events, rest }
}

export async function* postSse(
  url: string,
  body: object,
  signal?: AbortSignal,
): AsyncGenerator<SseEvent> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!response.ok) {
    throw new Error(`SSE request failed with status ${response.status}`)
  }
  if (!response.body) {
    throw new Error('SSE response body is unavailable')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let completed = false
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        completed = true
        buffer += decoder.decode()
        break
      }
      buffer += decoder.decode(value, { stream: true })
      const parsed = parseSseChunk(buffer)
      buffer = parsed.rest
      for (const event of parsed.events) yield event
    }

    if (buffer.trim()) {
      const parsed = parseSseChunk(`${buffer}\n\n`)
      for (const event of parsed.events) yield event
    }
  } finally {
    if (!completed) await reader.cancel()
    reader.releaseLock()
  }
}
