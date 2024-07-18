import {
  resolveColor,
  colorRecommendation,
} from '@baserow/modules/core/utils/colors'

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
    expect(
      resolveColor('#00000042', [
        { name: 'Default', value: '#00000042', color: '#00000042' },
      ])
    ).toBe('#00000042')
  })

  test('colorRecommendation', () => {
    expect(colorRecommendation('#FFFFFF')).toBe('gray')
    expect(colorRecommendation('#000000')).toBe('gray')
    expect(colorRecommendation('#FFFFFFFF')).toBe('gray')
    expect(colorRecommendation('#000000FF')).toBe('gray')
    expect(colorRecommendation('#5498db')).toBe('black')
    expect(colorRecommendation('#2c3e50')).toBe('white')
  })
})
