import { resolveColor } from '@baserow/modules/core/utils/colors'

describe('colorUtils', () => {
  test('resolve', () => {
    expect(resolveColor('#00000000', [])).toBe('#00000000')
    expect(resolveColor('test', [])).toBe('test')
    expect(
      resolveColor('primary', [
        { name: 'Primary', value: 'primary', color: '#ff000000' },
      ])
    ).toBe('#ff000000')
    expect(
      resolveColor('secondary', [
        { name: 'Primary', value: 'primary', color: '#ff000000' },
      ])
    ).toBe('secondary')
  })
})
