import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

import { TestApp } from '@baserow/test/helpers/testApp'
import DownloadLink from '@baserow/modules/core/components/DownloadLink'

const url = 'https://files.example.com/export_files/abc.zip'
const filename = 'Export.zip'

describe('DownloadLink', () => {
  let testApp = null
  let clicked = []

  beforeEach(() => {
    testApp = new TestApp()
    clicked = []
    // Records the anchors the component clicks itself, without navigating.
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(
      function () {
        clicked.push({
          href: this.href,
          download: this.download,
          target: this.target,
        })
      }
    )
    vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:file')
    vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {})
  })

  afterEach(async () => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
    await testApp.afterEach()
  })

  const mountComponent = (downloadFileViaXhr, props = {}) =>
    testApp.mount(DownloadLink, {
      props: { url, filename, loadingClass: 'is-loading', ...props },
      slots: { default: 'Download' },
      global: {
        mocks: { $config: { public: { downloadFileViaXhr } } },
      },
    })

  test('links to the file with its name without XHR', async () => {
    const wrapper = await mountComponent('0')
    const link = wrapper.find('a')

    const href = new URL(link.attributes('href'))
    expect(href.origin + href.pathname).toBe(url)
    expect(href.searchParams.get('dl')).toBe(filename)
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('download')).toBe(filename)
    expect(link.text()).toBe('Download')
  })

  test('fetches the file and saves it as a blob with XHR', async () => {
    let resolveFetch = null
    const fetch = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve
        })
    )
    vi.stubGlobal('fetch', fetch)
    const wrapper = await mountComponent('1')
    const link = wrapper.find('a')

    await link.trigger('click')

    expect(link.classes()).toContain('is-loading')
    expect(fetch).toHaveBeenCalledWith(url, { cache: 'no-store' })

    resolveFetch({ ok: true, blob: () => Promise.resolve(new Blob(['zip'])) })
    await flushPromises()

    expect(link.classes()).not.toContain('is-loading')
    expect(clicked).toStrictEqual([
      { href: 'blob:file', download: filename, target: '_blank' },
    ])
  })

  test('reports a non-ok response to onError without saving it', async () => {
    const blob = vi.fn(() => Promise.resolve(new Blob(['denied'])))
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 403, blob }))
    )
    const onError = vi.fn()
    const wrapper = await mountComponent('1', { onError })
    const link = wrapper.find('a')

    await link.trigger('click')
    await flushPromises()

    expect(onError).toHaveBeenCalledTimes(1)
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error)
    expect(onError.mock.calls[0][0].message).toContain('403')
    expect(blob).not.toHaveBeenCalled()
    expect(window.URL.createObjectURL).not.toHaveBeenCalled()
    expect(clicked).toStrictEqual([])
    expect(link.classes()).not.toContain('is-loading')
  })

  test('reports a failed fetch to onError', async () => {
    const error = new Error('Network error')
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(error))
    )
    const onError = vi.fn()
    const wrapper = await mountComponent('1', { onError })
    const link = wrapper.find('a')

    await link.trigger('click')
    await flushPromises()

    expect(onError).toHaveBeenCalledWith(error)
    expect(link.classes()).not.toContain('is-loading')
    expect(clicked).toStrictEqual([])
  })
})
