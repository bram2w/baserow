import { PremiumPlugin } from '@baserow_premium/plugins'

describe('Test premium Baserow plugin', () => {
  test('Test hasValidPremiumLicense method', () => {
    expect(
      PremiumPlugin.hasValidPremiumLicense({ premium: { valid_license: true } })
    ).toBe(true)
    expect(
      PremiumPlugin.hasValidPremiumLicense({
        premium: { valid_license: false },
      })
    ).toBe(false)
    expect(PremiumPlugin.hasValidPremiumLicense({ premium: {} })).toBe(false)
    expect(PremiumPlugin.hasValidPremiumLicense({})).toBe(false)

    // If the `valid_license` is `true`, the user has premium access features
    // enabled for all groups.
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        { premium: { valid_license: true } },
        1
      )
    ).toBe(true)
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        { premium: { valid_license: false } },
        1
      )
    ).toBe(false)

    // If the user only has premium access to certain groups, we expect false
    // for other groups.
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        { premium: { valid_license: [] } },
        1
      )
    ).toBe(false)
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        { premium: { valid_license: [{ type: 'group', id: 2 }] } },
        1
      )
    ).toBe(false)
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        {
          premium: {
            valid_license: [
              { type: 'group', id: 2 },
              { type: 'group', id: 3 },
            ],
          },
        },
        1
      )
    ).toBe(false)
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        {
          premium: {
            valid_license: [
              { type: 'group', id: 2 },
              { type: 'group', id: 3 },
            ],
          },
        },
        4
      )
    ).toBe(false)

    // If the user only has premium access to certain groups, he will not have
    // access to the premium features that are not related to a group.
    expect(
      PremiumPlugin.hasValidPremiumLicense({
        premium: { valid_license: [{ type: 'group', id: 1 }] },
      })
    ).toBe(false)
    expect(
      PremiumPlugin.hasValidPremiumLicense({
        premium: { valid_license: [{ type: 'group', id: 2 }] },
      })
    ).toBe(false)

    // If the user only has premium access to certain groups, we expect the
    // matches group to be true.
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        { premium: { valid_license: [{ type: 'group', id: 1 }] } },
        1
      )
    ).toBe(true)
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        {
          premium: {
            valid_license: [
              { type: 'group', id: 1 },
              { type: 'group', id: 2 },
            ],
          },
        },
        1
      )
    ).toBe(true)
    expect(
      PremiumPlugin.hasValidPremiumLicense(
        {
          premium: {
            valid_license: [
              { type: 'group', id: 1 },
              { type: 'group', id: 2 },
            ],
          },
        },
        2
      )
    ).toBe(true)
  })
})
