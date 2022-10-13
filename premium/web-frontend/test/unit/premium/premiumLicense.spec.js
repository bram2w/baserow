import { PremiumPlugin } from '@baserow_premium/plugins'
import { PremiumTestApp } from '@baserow_premium_test/helpers/premiumTestApp'
import { LicenseType } from '@baserow_premium/licenseTypes'

describe('Test premium licensing', () => {
  let testApp = null
  let premiumPluginUnderTest = null
  const fakeUserData = {
    user: {
      id: 256,
    },
    token:
      `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImpvaG5AZXhhb` +
      `XBsZS5jb20iLCJpYXQiOjE2NjAyOTEwODYsImV4cCI6MTY2MDI5NDY4NiwianRpIjo` +
      `iNDZmNzUwZWUtMTJhMS00N2UzLWJiNzQtMDIwYWM4Njg3YWMzIiwidXNlcl9pZCI6M` +
      `iwidXNlcl9wcm9maWxlX2lkIjpbMl0sIm9yaWdfaWF0IjoxNjYwMjkxMDg2fQ.RQ-M` +
      `NQdDR9zTi8CbbQkRrwNsyDa5CldQI83Uid1l9So`,
  }

  beforeAll(() => {
    testApp = new PremiumTestApp()
    premiumPluginUnderTest = new PremiumPlugin({ app: testApp.getApp() })
  })

  afterEach(() => {
    testApp.afterEach()
  })

  describe('test premium feature scenarios', () => {
    const testCases = [
      [
        'when user has global premium license they have active premium features',
        {
          whenUserDataIs: {
            premium: { valid_license: true },
          },
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
      [
        'when user does not have global premium license they dont have active' +
          ' premium features',
        {
          whenUserDataIs: {
            premium: { valid_license: false },
          },
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has invalid valid_license they dont have active premium features',
        {
          whenUserDataIs: {
            premium: { valid_license: {} },
          },
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has empty premium data they dont have active premium features',
        {
          whenUserDataIs: {
            premium: {},
          },
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has global premium they have premium features for any specific' +
          ' group',
        {
          whenUserDataIs: {
            premium: { valid_license: true },
          },
          forGroup: 1,
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
      [
        'when user has does not have global premium they dont have premium features' +
          ' for any specific group',
        {
          whenUserDataIs: {
            premium: { valid_license: false },
          },
          forGroup: 1,
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has license for no specific groups then other groups dont have ' +
          ' active premium features',
        {
          whenUserDataIs: {
            premium: { valid_license: [] },
          },
          forGroup: 1,
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has license for one specific group then other groups dont have ' +
          ' active premium features',
        {
          whenUserDataIs: {
            premium: { valid_license: [{ type: 'group', id: 1 }] },
          },
          forGroup: 2,
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has license for specific groups then other groups dont have ' +
          ' active premium features',
        {
          whenUserDataIs: {
            premium: {
              valid_license: [
                { type: 'group', id: 1 },
                { type: 'group', id: 3 },
              ],
            },
          },
          forGroup: 2,
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has license for specific groups then they wont have global premium' +
          ' active ',
        {
          whenUserDataIs: {
            premium: {
              valid_license: [{ type: 'group', id: 1 }],
            },
          },
          forGroup: undefined,
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when user has prem license for a specific group then for that group they' +
          ' will' +
          ' have active premium features.',
        {
          whenUserDataIs: {
            premium: {
              valid_license: [{ type: 'group', id: 1 }],
            },
          },
          forGroup: 1,
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
      [
        'when user has prem license for two groups then for one of those ' +
          ' groups they will have have active premium features.',
        {
          whenUserDataIs: {
            premium: {
              valid_license: [
                { type: 'group', id: 1 },
                { type: 'group', id: 2 },
              ],
            },
          },
          forGroup: 2,
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
      [
        'when user has prem license for multiple groups then for one of those ' +
          ' groups they will have have active premium features.',
        {
          whenUserDataIs: {
            premium: {
              valid_license: [
                { type: 'group', id: 1 },
                { type: 'group', id: 2 },
                { type: 'group', id: 3 },
              ],
            },
          },
          forGroup: 1,
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
    ]

    test.each(testCases)('test %s', (name, testCaseSpecification) => {
      testApp.store.dispatch('auth/forceSetUserData', {
        ...fakeUserData,
        ...testCaseSpecification.whenUserDataIs,
      })
      expect(
        premiumPluginUnderTest.activeLicenseHasPremiumFeatures(
          testCaseSpecification.forGroup
        )
      ).toBe(testCaseSpecification.thenActiveLicenseHasPremiumFeaturesIs)
    })
  })

  describe('test premium feature with a plugin scenarios', () => {
    class StubLicenseType extends LicenseType {
      constructor({
        hasPremiumFeatures,
        isActiveGlobally,
        activeForGroups = null,
        app,
      }) {
        super({ app })
        this.stubHasPremiumFeatures = hasPremiumFeatures
        this.isActiveGlobally = isActiveGlobally
        this.activeForGroups = activeForGroups || []
      }

      static getType() {
        return 'stub'
      }

      getName() {
        return 'stub'
      }

      hasPremiumFeatures() {
        return this.stubHasPremiumFeatures
      }

      hasValidActiveLicense(forGroupId = undefined) {
        if (this.isActiveGlobally) {
          return true
        } else {
          return this.activeForGroups.includes(forGroupId)
        }
      }
    }

    const testCases = [
      [
        'test custom license type that is active with premium features grants the' +
          ' user premium.',
        {
          whenUserDataIs: {
            premium: {
              valid_license: false,
            },
          },
          extraLicenseTypes: [
            (testApp) =>
              new StubLicenseType({
                hasPremiumFeatures: true,
                isActiveGlobally: true,
                app: testApp.getApp(),
              }),
          ],
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
      [
        'test custom license type that is active without premium features does not ' +
          'grant the user premium',
        {
          whenUserDataIs: {
            premium: {
              valid_license: false,
            },
          },
          extraLicenseTypes: [
            (testApp) =>
              new StubLicenseType({
                hasPremiumFeatures: false,
                isActiveGlobally: true,
                app: testApp.getApp(),
              }),
          ],
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'test no active license granting premium features means user has no premium',
        {
          whenUserDataIs: {
            premium: {
              valid_license: false,
            },
          },
          extraLicenseTypes: [
            (testApp) =>
              new StubLicenseType({
                hasPremiumFeatures: true,
                isActiveGlobally: false,
                app: testApp.getApp(),
              }),
          ],
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
      [
        'when custom license type active for specific group and it grants premium' +
          ' then the user gets premium for that group.',
        {
          whenUserDataIs: {
            premium: {
              valid_license: false,
            },
          },
          extraLicenseTypes: [
            (testApp) =>
              new StubLicenseType({
                hasPremiumFeatures: true,
                isActiveGlobally: false,
                activeForGroups: [1],
                app: testApp.getApp(),
              }),
          ],
          forGroup: 1,
          thenActiveLicenseHasPremiumFeaturesIs: true,
        },
      ],
      [
        'when custom license type active for specific group and it grants premium' +
          ' then the user does not get premium for other groups',
        {
          whenUserDataIs: {
            premium: {
              valid_license: false,
            },
          },
          extraLicenseTypes: [
            (testApp) =>
              new StubLicenseType({
                hasPremiumFeatures: true,
                isActiveGlobally: false,
                activeForGroups: [1],
                app: testApp.getApp(),
              }),
          ],
          forGroup: 2,
          thenActiveLicenseHasPremiumFeaturesIs: false,
        },
      ],
    ]

    test.each(testCases)('%s', (name, testCaseSpecification) => {
      const registry = testApp.getRegistry()
      for (const extraLicenseType of testCaseSpecification.extraLicenseTypes) {
        registry.register('license', extraLicenseType(testApp))
      }
      testApp.store.dispatch('auth/forceSetUserData', {
        ...fakeUserData,
        ...testCaseSpecification.whenUserDataIs,
      })
      expect(
        premiumPluginUnderTest.activeLicenseHasPremiumFeatures(
          testCaseSpecification.forGroup
        )
      ).toBe(testCaseSpecification.thenActiveLicenseHasPremiumFeaturesIs)
    })
  })
})
