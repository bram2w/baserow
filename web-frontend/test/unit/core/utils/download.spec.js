import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import {
  downloadViaXhr,
  getDownloadHref,
  triggerDownload,
} from '@baserow/modules/core/utils/download'

const url = 'https://files.example.com/template-revisions/abc.zip'
const filename = 'sales-pipeline.zip'

describe('download', () => {
  let clicked = []

  beforeEach(() => {
    clicked = []
    // Records the clicked anchors, without navigating.
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(
      function () {
        clicked.push(this)
      }
    )
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:file')
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  const stubActivation = (isActive) =>
    vi.stubGlobal(
      'navigator',
      Object.create(navigator, { userActivation: { value: { isActive } } })
    )

  // The click of the anchor must not close the menu or modal it's started from.
  const expectStopsPropagation = (anchor) => {
    const event = { stopPropagation: vi.fn() }
    anchor.onclick(event)
    expect(event.stopPropagation).toHaveBeenCalled()
  }

  test('getDownloadHref adds the file name to the URL', () => {
    const href = new URL(getDownloadHref(`${url}?token=1`, filename))

    expect(href.origin + href.pathname).toBe(url)
    expect(href.searchParams.get('dl')).toBe(filename)
    expect(href.searchParams.get('token')).toBe('1')
  })

  test('downloadViaXhr saves the fetched file as a blob', async () => {
    const fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(['zip'])),
      })
    )
    vi.stubGlobal('fetch', fetch)

    await downloadViaXhr(url, filename)

    expect(fetch).toHaveBeenCalledWith(url, { cache: 'no-store' })
    expect(clicked).toHaveLength(1)
    expect(clicked[0].href).toBe('blob:file')
    expect(clicked[0].download).toBe(filename)
    expectStopsPropagation(clicked[0])
  })

  test.each([403, 404])(
    'downloadViaXhr throws on a %i response without saving it',
    async (status) => {
      const blob = vi.fn(() => Promise.resolve(new Blob(['error'])))
      vi.stubGlobal(
        'fetch',
        vi.fn(() => Promise.resolve({ ok: false, status, blob }))
      )

      await expect(downloadViaXhr(url, filename)).rejects.toThrow(
        String(status)
      )

      expect(blob).not.toHaveBeenCalled()
      expect(clicked).toHaveLength(0)
    }
  )

  test('triggerDownload saves the file through XHR when asked', async () => {
    const fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(['zip'])),
      })
    )
    vi.stubGlobal('fetch', fetch)

    await triggerDownload(url, filename, { viaXhr: true })

    expect(fetch).toHaveBeenCalledWith(url, { cache: 'no-store' })
    expect(clicked.map((anchor) => anchor.href)).toStrictEqual(['blob:file'])
  })

  test.each([
    ['the activation is unknown', null],
    ['the user activation is active', true],
  ])(
    'triggerDownload opens the file in a new tab when %s',
    async (_, isActive) => {
      if (isActive !== null) {
        stubActivation(isActive)
      }
      const fetch = vi.fn()
      vi.stubGlobal('fetch', fetch)

      await triggerDownload(url, filename)

      expect(fetch).not.toHaveBeenCalled()
      expect(clicked).toHaveLength(1)
      const [anchor] = clicked
      expect(new URL(anchor.href).searchParams.get('dl')).toBe(filename)
      expect(anchor.target).toBe('_blank')
      expect(anchor.download).toBe(filename)
      expectStopsPropagation(anchor)
      // The anchor is removed again.
      expect(anchor.isConnected).toBe(false)
    }
  )

  test('triggerDownload stays in the tab once the user activation expired', async () => {
    stubActivation(false)

    await triggerDownload(url, filename)

    expect(clicked).toHaveLength(1)
    const [anchor] = clicked
    expect(new URL(anchor.href).searchParams.get('dl')).toBe(filename)
    expect(anchor.target).toBe('')
    expect(anchor.download).toBe(filename)
    expectStopsPropagation(anchor)
  })
})
