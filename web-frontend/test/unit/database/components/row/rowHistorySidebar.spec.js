import { TestApp } from '@baserow/test/helpers/testApp'
import RowHistorySidebar from '@baserow/modules/database/components/row/RowHistorySidebar'
import { registerRealtimeEvents } from '@baserow/modules/database/realtime'
import { nextTick } from 'vue'

describe('row history reconnect recovery', () => {
  let testApp
  let completed
  const url = '/database/rows/table/1/2/history/'
  const entry = (id) => ({
    id,
    timestamp: '2026-09-08T10:00:00Z',
    before: {},
    after: {},
    fields_metadata: {},
    action_type: 'create_row',
  })
  const response = (id) => [200, { results: [entry(id)], count: 1 }]

  beforeEach(() => {
    testApp = new TestApp()
    registerRealtimeEvents({
      registerEvent(name, handler) {
        if (name === 'replay_completed') completed = handler
      },
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mount = () =>
    testApp.mount(RowHistorySidebar, {
      props: {
        database: { workspace: { id: 1 } },
        table: { id: 1 },
        row: { id: 2 },
        fields: [],
      },
      global: {
        stubs: {
          InfiniteScroll: { template: '<div><slot /></div>' },
          RowHistoryEntry: {
            props: ['entry'],
            template: '<span class="history-entry">{{ entry.id }}</span>',
          },
        },
      },
    })

  test('refetches an open sidebar after reconnect but not a fresh baseline', async () => {
    let id = 10
    testApp.mock.onGet(url).reply(() => response(id))
    const wrapper = await mount()
    await vi.waitFor(() =>
      expect(wrapper.find('.history-entry').text()).toBe('10')
    )
    completed({ store: testApp.store }, { is_reconnect: false })
    expect(testApp.mock.history.get).toHaveLength(1)
    id = 11
    completed({ store: testApp.store }, { is_reconnect: true })
    await vi.waitFor(() =>
      expect(wrapper.find('.history-entry').text()).toBe('11')
    )
    expect(testApp.mock.history.get).toHaveLength(2)
    expect(
      testApp.mock.history.get[1].headers['X-Baserow-Realtime-Recovery']
    ).toBe('true')
  })

  test('keeps hidden history stale without fetching until it opens', async () => {
    testApp.mock.onGet(url).reply(...response(12))
    completed({ store: testApp.store }, { is_reconnect: true })
    expect(testApp.mock.history.get).toHaveLength(0)
    const wrapper = await mount()
    await vi.waitFor(() =>
      expect(wrapper.find('.history-entry').text()).toBe('12')
    )
    expect(
      testApp.mock.history.get[0].headers['X-Baserow-Realtime-Recovery']
    ).toBe('true')
    wrapper.unmount()
    completed({ store: testApp.store }, { is_reconnect: true })
    expect(testApp.mock.history.get).toHaveLength(1)
    expect(testApp.store.getters['rowHistory/getLoaded']).toBe(false)
  })

  test.each([false, true])(
    'a failed history load shows a local retry and preserves cached entries: %s',
    async (hasCachedEntries) => {
      testApp.dontFailOnErrorResponses()
      if (hasCachedEntries) {
        testApp.mock.onGet(url).replyOnce(...response(10))
      }
      testApp.mock.onGet(url).replyOnce(503, {})
      testApp.mock.onGet(url).replyOnce(...response(11))
      const wrapper = await mount()
      if (hasCachedEntries) {
        await vi.waitFor(() =>
          expect(wrapper.find('.history-entry').text()).toBe('10')
        )
        completed({ store: testApp.store }, { is_reconnect: true })
      }
      await vi.waitFor(() =>
        expect(wrapper.find('.alert--error').exists()).toBe(true)
      )
      expect(wrapper.find('.row-history__empty').exists()).toBe(false)
      expect(
        wrapper.findAll('.history-entry').map((entry) => entry.text())
      ).toEqual(hasCachedEntries ? ['10'] : [])
      expect(testApp.store.getters['rowHistory/getLoaded']).toBe(false)
      await wrapper.find('.alert--error button').trigger('click')
      await vi.waitFor(() =>
        expect(wrapper.find('.history-entry').text()).toBe('11')
      )
      expect(wrapper.find('.alert--error').exists()).toBe(false)
      expect(testApp.store.getters['rowHistory/getLoaded']).toBe(true)
      expect(
        testApp.mock.history.get.at(-1).headers['X-Baserow-Realtime-Recovery']
      ).toBe('true')
    }
  )

  test('coalesces reconnects during a request into one trailing snapshot', async () => {
    const replies = []
    testApp.mock.onGet(url).reply(
      () =>
        new Promise((resolve) => {
          replies.push(resolve)
        })
    )
    const wrapper = await mount()
    await vi.waitFor(() => expect(replies).toHaveLength(1))
    completed({ store: testApp.store }, { is_reconnect: true })
    completed({ store: testApp.store }, { is_reconnect: true })
    await nextTick()
    expect(replies).toHaveLength(1)
    replies[0](response(10))
    await vi.waitFor(() => expect(replies).toHaveLength(2))
    replies[1](response(11))
    await vi.waitFor(() =>
      expect(wrapper.find('.history-entry').text()).toBe('11')
    )
    expect(testApp.mock.history.get).toHaveLength(2)
  })

  test('unmounting stops a pending trailing recovery request', async () => {
    const replies = []
    testApp.mock.onGet(url).reply(
      () =>
        new Promise((resolve) => {
          replies.push(resolve)
        })
    )
    const wrapper = await mount()
    await vi.waitFor(() => expect(replies).toHaveLength(1))
    completed({ store: testApp.store }, { is_reconnect: true })
    await nextTick()
    wrapper.unmount()
    replies[0](response(10))
    await vi.waitFor(() =>
      expect(testApp.store.getters['rowHistory/getLoading']).toBe(false)
    )
    expect(testApp.store.getters['rowHistory/getLoaded']).toBe(false)
    expect(testApp.mock.history.get).toHaveLength(1)
  })
})
