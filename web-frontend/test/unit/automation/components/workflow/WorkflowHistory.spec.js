import { mountSuspended } from '@nuxt/test-utils/runtime'
import WorkflowHistory from '@baserow/modules/automation/components/workflow/sidePanels/WorkflowHistory.vue'

// WorkflowHistory reads the node histories from the automationHistory store
// and dispatches fetches on toggle; neither matters for the header, so the
// store is a stub. See WorkflowEdge.spec.js for why only useStore is mocked.
const storeHolder = vi.hoisted(() => ({ store: null }))
vi.mock('vuex', async (importOriginal) => ({
  ...(await importOriginal()),
  useStore: () => storeHolder.store,
}))

const mountHistory = (item, usersById = {}) => {
  storeHolder.store = {
    dispatch: vi.fn(),
    getters: {
      'automationHistory/getNodeHistories': () => null,
      'workspace/getAll': [{ id: 1 }],
      'workspace/getUserById': (id) => usersById[id] ?? null,
    },
  }
  return mountSuspended(WorkflowHistory, {
    props: { item },
    global: { stubs: { NodeHistory: true } },
  })
}

const baseItem = {
  id: 1,
  status: 'success',
  started_on: '2026-09-09T10:00:00Z',
  completed_on: '2026-09-09T10:00:02Z',
  is_test_run: false,
  message: '',
  triggered_by: null,
}

describe('WorkflowHistory', () => {
  afterEach(() => {
    storeHolder.store = null
  })

  // The test app has no locale messages loaded, so `$t` returns the key.
  test('names who started the run from the workspace store', async () => {
    const wrapper = await mountHistory(
      { ...baseItem, triggered_by: { id: 7, name: 'Ada' } },
      { 7: { id: 7, name: 'Ada Lovelace' } }
    )
    expect(wrapper.find('.workflow-history__actor').text()).toBe(
      'historySidePanel.startedBy'
    )
  })

  test('still names a user who left the workspace', async () => {
    const wrapper = await mountHistory({
      ...baseItem,
      triggered_by: { id: 7, name: 'Ada' },
    })
    expect(wrapper.find('.workflow-history__actor').exists()).toBe(true)
  })

  test('shows nothing when nobody is recorded', async () => {
    const wrapper = await mountHistory(baseItem)
    expect(wrapper.find('.workflow-history__actor').exists()).toBe(false)
  })
})
