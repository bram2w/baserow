import {
  getReferencedDashboardFilterId,
  hasActiveDashboardFilter,
} from '@baserow/modules/dashboard/utils/filter'

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

test.each([
  ["get('dashboard_filter.12')", ['France'], true],
  ["get('dashboard_filter.12')", [], false],
  ["get('dashboard_filter.12')", ['  '], false],
  ["get('dashboard_filter.12.*')", ['France', 'Belgium'], true],
  ["get('dashboard_filter.12.1')", ['France'], false],
  ["get('dashboard_filter.12.1')", ['France', 'Belgium'], true],
  ["get('dashboard_filter.13')", ['France'], false],
  ["concat(get('dashboard_filter.12'), '')", ['France'], true],
  ["'dashboard_filter.12'", ['France'], false],
  ['"get(\'dashboard_filter.12\')"', ['France'], false],
  ["get('table.12')", ['France'], false],
  ["get('dashboard_filter.12", ['France'], false],
])(
  'detects an active dashboard filter in %s with %j',
  (formula, values, expected) => {
    expect(
      hasActiveDashboardFilter(
        { formula, mode: 'simple' },
        [{ id: 12, mode: 'dropdown', multiple: true }],
        { 12: values }
      )
    ).toBe(expected)
  }
)

test.each(['empty', 'not_empty'])(
  'recognizes a %s condition only when activated',
  (operator) => {
    const formula = { formula: "get('dashboard_filter.12')", mode: 'simple' }
    const filters = [{ id: 12, mode: 'input', operator }]
    expect(hasActiveDashboardFilter(formula, filters, { 12: [] })).toBe(false)
    expect(hasActiveDashboardFilter(formula, filters, { 12: ['true'] })).toBe(
      true
    )
  }
)

test('ignores a removed control and raw text when values are still cached', () => {
  const formula = { formula: "get('dashboard_filter.12')", mode: 'simple' }
  expect(hasActiveDashboardFilter(formula, [], { 12: ['France'] })).toBe(false)
  expect(
    hasActiveDashboardFilter(
      { ...formula, mode: 'raw' },
      [{ id: 12, mode: 'input' }],
      { 12: ['France'] }
    )
  ).toBe(false)
})
