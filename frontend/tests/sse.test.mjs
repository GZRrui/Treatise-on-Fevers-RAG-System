import assert from 'node:assert/strict'
import test from 'node:test'

import { parseSseChunk } from '../src/api/sse.ts'

test('parses complete events and retains a partial frame', () => {
  const first = parseSseChunk(
    'data: {"type":"content","data":"你"}\n\n' +
      'data: {"type":"content"',
  )

  assert.deepEqual(first.events, [{ type: 'content', data: '你' }])
  assert.equal(first.rest, 'data: {"type":"content"')

  const second = parseSseChunk(`${first.rest},"data":"好"}\n\n`)
  assert.deepEqual(second.events, [{ type: 'content', data: '好' }])
  assert.equal(second.rest, '')
})

test('supports CRLF frames and the single end event', () => {
  const parsed = parseSseChunk(
    'data: {"type":"sources","data":[]}\r\n\r\n' +
      'data: {"type":"end","data":"完成"}\r\n\r\n',
  )

  assert.deepEqual(
    parsed.events.map((event) => event.type),
    ['sources', 'end'],
  )
})

test('rejects payloads without an event type', () => {
  assert.throws(
    () => parseSseChunk('data: {"data":"invalid"}\n\n'),
    /Invalid SSE event payload/,
  )
})
