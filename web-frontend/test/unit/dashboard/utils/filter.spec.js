import { getReferencedDashboardFilterId } from '@baserow/modules/dashboard/utils/filter'

test.each([
  ["get('dashboard_filter.12')", 12],
  [' GET("dashboard_filter.12") ', 12],
  ["get( 'dashboard_filter.12' )", 12],
  ["get(('dashboard_filter.12'))", 12],
  ["(get('dashboard_filter.12'))", 12],
  ["get('dashboard_filter.12.*')", 12],
  ["get('dashboard_filter.12.1')", 12],
  ["concat(get('dashboard_filter.12'), '')", null],
  ["get('dashboard_filter.12') + get('dashboard_filter.13')", null],
  ["get('table.12')", null],
  ["get('dashboard_filter.0')", null],
  ["get('dashboard_filter.12", null],
])(
  'identifies the control for %s without treating calculations as links',
  (formula, expected) => {
    expect(getReferencedDashboardFilterId({ formula, mode: 'simple' })).toBe(
      expected
    )
  }
)

test('literal text that looks like a control reference stays literal', () => {
  expect(
    getReferencedDashboardFilterId({
      formula: "get('dashboard_filter.12')",
      mode: 'raw',
    })
  ).toBeNull()
})
