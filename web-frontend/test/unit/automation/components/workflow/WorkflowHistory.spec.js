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

const mountHistory = (item) => {
  storeHolder.store = {
    dispatch: vi.fn(),
    getters: {
      'automationHistory/getNodeHistories': () => null,
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

  test('names who started the run', async () => {
    const wrapper = await mountHistory({
      ...baseItem,
      triggered_by: { id: 7, first_name: 'Ada' },
    })
    // The test app has no locale messages loaded, so `$t` returns the key;
    // the name travels through the tooltip.
    const actor = wrapper.find('.workflow-history__header-actor')
    expect(actor.text()).toBe('historySidePanel.startedBy')
    expect(actor.attributes('title')).toBe('Ada')
  })

  test('shows nothing when nobody is recorded', async () => {
    const wrapper = await mountHistory(baseItem)
    expect(wrapper.find('.workflow-history__header-actor').exists()).toBe(false)
  })
})
