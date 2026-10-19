import { mount } from '@vue/test-utils'

import PublicDashboard from '@baserow/modules/dashboard/components/PublicDashboard'

function mountPublicDashboard({
  dashboard = {},
  isEmpty = false,
  loading = false,
} = {}) {
  return mount(PublicDashboard, {
    props: {
      dashboard: {
        id: 1,
        name: 'Conversion compass',
        description: 'Tracking conversion rates at every stage.',
        show_logo: true,
        workspace: { id: 0 },
        ...dashboard,
      },
      loading,
    },
    global: {
      mocks: {
        $t: (key) => key,
      },
      provide: {
        store: {
          getters: {
            'dashboardApplication/isEmpty': isEmpty,
          },
        },
      },
      stubs: {
        WidgetBoard: {
          template: '<div data-testid="widget-board"></div>',
        },
        DashboardWidgetGridLoading: {
          template: '<div data-testid="widget-grid-loading"></div>',
        },
        ExternalLinkBaserowLogo: {
          template: '<a data-testid="baserow-logo"></a>',
        },
      },
    },
  })
}

describe('PublicDashboard', () => {
  test('shows the name, the description, the widgets and the Baserow logo', () => {
    const wrapper = mountPublicDashboard()

    expect(wrapper.get('.dashboard-app__title').text()).toBe(
      'Conversion compass'
    )
    expect(wrapper.get('.dashboard-app__description').text()).toBe(
      'Tracking conversion rates at every stage.'
    )
    expect(wrapper.find('[data-testid="widget-board"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="baserow-logo"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="widget-grid-loading"]').exists()).toBe(
      false
    )
  })

  test('hides the Baserow logo when the owner switched it off', () => {
    const wrapper = mountPublicDashboard({ dashboard: { show_logo: false } })

    expect(wrapper.find('[data-testid="baserow-logo"]').exists()).toBe(false)
  })

  test('leaves out an empty description', () => {
    const wrapper = mountPublicDashboard({ dashboard: { description: '' } })

    expect(wrapper.find('.dashboard-app__description').exists()).toBe(false)
  })

  test('shows the loading state instead of the widgets while loading', () => {
    const wrapper = mountPublicDashboard({ loading: true })

    expect(wrapper.find('[data-testid="widget-grid-loading"]').exists()).toBe(
      true
    )
    expect(wrapper.find('[data-testid="widget-board"]').exists()).toBe(false)
  })

  test('tells visitors when the dashboard has no widgets', () => {
    const wrapper = mountPublicDashboard({ isEmpty: true })

    expect(wrapper.get('.public-dashboard__empty').text()).toBe(
      'publicDashboard.noWidgets'
    )
    expect(wrapper.find('[data-testid="widget-board"]').exists()).toBe(false)
  })
})
