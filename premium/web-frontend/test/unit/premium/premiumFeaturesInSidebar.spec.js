import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'
import { PremiumTestApp } from '@baserow_premium_test/helpers/premiumTestApp'
import { PremiumUIHelpers } from '@baserow_premium_test/helpers/premiumUIHelpers'
import { UIHelpers } from '@baserow/test/helpers/testApp'

describe('Sidebar Premium Features Snapshot tests', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new PremiumTestApp()
    testApp.createTestUserInAuthStore()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test(
    'When user does not have global premium enabled the sidebar does not show a' +
      ' premium badge',
    async () => {
      const sidebarComponent = await testApp.mount(Sidebar, {})
      expect(
        PremiumUIHelpers.sidebarShowsPremiumEnabled(sidebarComponent)
      ).toBe(false)
    }
  )

  test(
    'When user does have global premium enabled the sidebar does show a premium' +
      ' badge',
    async () => {
      testApp.giveCurrentUserGlobalPremiumFeatures()
      const sidebarComponent = await testApp.mount(Sidebar, {})
      expect(
        PremiumUIHelpers.sidebarShowsPremiumEnabled(sidebarComponent)
      ).toBe(true)
    }
  )

  test('A realtime update to global premium is reflected in the badge', async () => {
    const sidebarComponent = await testApp.mount(Sidebar, {})
    expect(PremiumUIHelpers.sidebarShowsPremiumEnabled(sidebarComponent)).toBe(
      false
    )
    testApp.giveCurrentUserGlobalPremiumFeatures()
    await sidebarComponent.vm.$nextTick()
    expect(PremiumUIHelpers.sidebarShowsPremiumEnabled(sidebarComponent)).toBe(
      true
    )
  })

  test('When user is staff without global premium they dont see a premium badge', async () => {
    testApp.updateCurrentUserToBecomeStaffMember()
    const sidebarComponent = await testApp.mount(Sidebar, {})
    expect(PremiumUIHelpers.sidebarShowsPremiumEnabled(sidebarComponent)).toBe(
      false
    )
  })

  test('When user is staff with global premium they see a premium badge', async () => {
    testApp.giveCurrentUserGlobalPremiumFeatures()
    testApp.updateCurrentUserToBecomeStaffMember()
    const sidebarComponent = await testApp.mount(Sidebar, {})
    expect(PremiumUIHelpers.sidebarShowsPremiumEnabled(sidebarComponent)).toBe(
      true
    )
  })

  test('A non staff user cannot see admin settings links', async () => {
    const sidebarComponent = await testApp.mount(Sidebar, {})
    expect(UIHelpers.getSidebarItemNames(sidebarComponent)).not.toContain(
      'sidebar.admin'
    )
  })

  test('A non staff user with group premium cannot see admin settings links', async () => {
    testApp.giveCurrentUserPremiumFeatureForSpecificGroupOnly(1)
    testApp
      .getStore()
      .dispatch('group/forceCreate', { id: 1, name: 'testGroup' })
    const sidebarComponent = await testApp.mount(Sidebar, {})
    expect(UIHelpers.getSidebarItemNames(sidebarComponent)).not.toContain(
      'sidebar.admin'
    )
  })

  test('A staff user can see admin settings links', async () => {
    testApp.updateCurrentUserToBecomeStaffMember()
    const sidebarComponent = await testApp.mount(Sidebar, {})
    expect(UIHelpers.getSidebarItemNames(sidebarComponent)).toContain(
      'sidebar.admin'
    )
  })

  test('A staff user without global prem sees premium admin options locked', async () => {
    testApp.updateCurrentUserToBecomeStaffMember()
    testApp.setRouteToBe('admin-dashboard')
    const sidebarComponent = await testApp.mount(Sidebar, {})
    await UIHelpers.selectSidebarItem(sidebarComponent, 'sidebar.admin')
    expect(UIHelpers.getDisabledSidebarItemNames(sidebarComponent)).toEqual(
      expect.arrayContaining([
        'sidebar.admin',
        'premium.adminType.dashboard',
        'premium.adminType.users',
        'premium.adminType.groups',
      ])
    )
  })

  test('A staff user with global prem sees premium admin options available', async () => {
    const openedPage = 'sidebar.admin'
    testApp.updateCurrentUserToBecomeStaffMember()
    testApp.giveCurrentUserGlobalPremiumFeatures()
    testApp.setRouteToBe('admin-dashboard')

    const sidebarComponent = await testApp.mount(Sidebar, {})
    await UIHelpers.selectSidebarItem(sidebarComponent, openedPage)

    expect(
      UIHelpers.getDisabledSidebarItemNames(sidebarComponent)
    ).toStrictEqual([openedPage])
    const sidebarItemNames = UIHelpers.getSidebarItemNames(sidebarComponent)
    expect(sidebarItemNames).toEqual(
      expect.arrayContaining([
        openedPage,
        'premium.adminType.dashboard',
        'premium.adminType.users',
        'premium.adminType.groups',
      ])
    )
  })
})
