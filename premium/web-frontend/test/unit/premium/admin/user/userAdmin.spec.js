import { TestApp } from '@baserow/test/helpers/testApp'
import UserAdminTable from '@baserow_premium/components/admin/user/UserAdminTable'
import moment from 'moment'
import flushPromises from 'flush-promises'
import UserAdminUserHelpers from '../../../../fixtures/uiHelpers'
import MockPremiumServer from '@baserow_premium/../../test/fixtures/mockPremiumServer'

// Mock out debounce so we dont have to wait or simulate waiting for the various
// debounces in the search functionality.
jest.mock('lodash/debounce', () => jest.fn((fn) => fn))

describe('User Admin Component Tests', () => {
  let testApp = null
  let mockPremiumServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockPremiumServer = new MockPremiumServer(testApp.mock)
  })

  afterEach(() => testApp.afterEach())

  test('A users attributes will be displayed', async () => {
    const userSetup = {
      id: 1,
      username: 'user@baserow.io',
      name: 'user name',
      groups: [
        {
          id: 4,
          name: "users's group",
          permissions: 'ADMIN',
        },
        {
          id: 65,
          name: 'other_group',
        },
      ],
      lastLogin: '2021-04-26T07:50:45.643059Z',
      dateJoined: '2021-04-21T12:04:27.379781Z',
      isActive: true,
      isStaff: true,
    }
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin(userSetup)

    const cells = ui.findCells()
    expect(cells.length).toBe(7)
    const {
      userIdCell,
      usernameCell,
      nameCell,
      groupsCell,
      lastLoginCell,
      signedUpCell,
      isActiveCell,
    } = ui.getRow(cells, 0)

    expect(userIdCell.text()).toBe('1')

    // Username matches with correct initials and has an admin icon
    expect(usernameCell.text()).toContain(userSetup.username)
    expect(ui.usernameCellIsForStaffMember(usernameCell)).toBe(true)
    expect(ui.getUsernameInitials(usernameCell)).toBe('UN')

    // First name matches
    expect(nameCell.text()).toBe(userSetup.name)

    // Has two groups
    const groups = ui.getGroups(groupsCell)
    expect(groups.length).toBe(2)
    const firstGroup = groups.at(0)
    const secondGroup = groups.at(1)

    // The first group has the correct name and as the user is an admin an icon is
    // displayed
    expect(firstGroup.text()).toBe("users's group")
    expect(ui.groupCellShowsThisUserIsGroupAdmin(firstGroup)).toBe(true)

    // The second group has the right name and no admin icon as the user is not an
    // admin
    expect(secondGroup.text()).toBe('other_group')
    expect(ui.groupCellShowsThisUserIsGroupAdmin(secondGroup)).toBe(false)

    // The last login and signed up dates are correctly formatted to the locale
    moment.locale('nl')
    expect(lastLoginCell.text()).toBe('04/26/2021 7:50 AM')
    expect(signedUpCell.text()).toBe('04/21/2021 12:04 PM')

    // Shown as active
    expect(isActiveCell.text()).toBe('Active')
  })

  test('A user with no groups is displayed without any', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      groups: [],
    })

    await flushPromises()

    const cells = ui.findCells()
    expect(cells.length).toBe(7)
    const { usernameCell, groupsCell } = ui.getRow(cells, 0)

    expect(usernameCell.text()).toContain(user.username)
    const groups = ui.getGroups(groupsCell)
    expect(groups.length).toBe(0)
  })

  test('A user can be deleted', async () => {
    const { user, userAdmin, ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    expect(userAdmin.html()).toContain(user.username)

    const editUserContext = await ui.openFirstUserActionsMenu()
    await ui.clickDeleteUser(editUserContext)

    mockPremiumServer.expectUserDeleted(user.id)

    await ui.clickConfirmDeleteUserInModal()

    await flushPromises()

    expect(userAdmin.html()).not.toContain(user.username)
  })

  test('An active user can be deactivated', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      isActive: true,
    })

    const editUserContext = await ui.openFirstUserActionsMenu()

    mockPremiumServer.expectUserUpdated(user, {
      is_active: false,
    })

    await ui.clickDeactivateUser(editUserContext)

    await flushPromises()

    const cells = ui.findCells()
    const { isActiveCell } = ui.getRow(cells, 0)
    expect(isActiveCell.text()).toContain('Deactivated')
  })

  test('A deactivated user can be activated', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      isActive: false,
    })

    const editUserContext = await ui.openFirstUserActionsMenu()

    mockPremiumServer.expectUserUpdated(user, {
      is_active: true,
    })

    await ui.clickActivateUser(editUserContext)

    await flushPromises()

    const cells = ui.findCells()
    const { isActiveCell } = ui.getRow(cells, 0)
    expect(isActiveCell.text()).toContain('Active')
  })

  test('A users password can be changed', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const newValidPassword = '12345678'
    mockPremiumServer.expectUserUpdated(user, {
      password: newValidPassword,
    })

    await ui.changePassword(newValidPassword, newValidPassword)

    await flushPromises()
  })

  test('users password cant be changed if not entered the same twice', async () => {
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const validPassword = '1'.repeat(8)

    expect(
      await ui.attemptToChangePasswordReturningModalError(
        validPassword,
        validPassword + 'DifferentFromFirst'
      )
    ).toContain('This field must match your password field')
  })

  test('users password cant be changed less than 8 characters', async () => {
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const tooShortPassword = '1'.repeat(7)

    expect(
      await ui.attemptToChangePasswordReturningModalError(
        tooShortPassword,
        tooShortPassword
      )
    ).toContain('A minimum of 8 characters is required here.')
  })

  test('users password cant be changed to more than 256 characters', async () => {
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const tooLongPassword = '1'.repeat(257)

    expect(
      await ui.attemptToChangePasswordReturningModalError(
        tooLongPassword,
        tooLongPassword
      )
    ).toContain('A maximum of 256 characters is allowed here.')
  })

  test('users password can be changed to 256 characters', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const longestValidPassword = '1'.repeat(256)
    mockPremiumServer.expectUserUpdated(user, {
      password: longestValidPassword,
    })

    await ui.changePassword(longestValidPassword, longestValidPassword)

    await flushPromises()
  })

  test('changing a users password displays an error if the server responds with one', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const validPassword = '1'.repeat(8)

    testApp.dontFailOnErrorResponses()

    mockPremiumServer.expectUserUpdatedRespondsWithError(user, {
      error: 'SOME_ERROR',
      detail: 'Some error text',
    })

    const modal = await ui.changePassword(validPassword, validPassword)

    await flushPromises()

    expect(ui.getErrorText(modal)).toBe(
      "The action couldn't be completed because an unknown error has occured."
    )
  })

  test('a users full name can be changed', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      name: 'Old Full Name',
    })

    const newFullName = 'New Full Name'
    mockPremiumServer.expectUserUpdated(user, {
      name: newFullName,
      // Expect the other edit modal fields will be sent, just with no changes.
      is_staff: user.is_staff,
      is_active: user.is_active,
      username: user.username,
    })

    await ui.changeFullName(newFullName)

    await flushPromises()

    const cells = ui.findCells()
    const { nameCell } = ui.getRow(cells, 0)
    expect(nameCell.text()).toContain(newFullName)
  })

  test('when an server error is returned when editing a user it is shown', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({})

    testApp.dontFailOnErrorResponses()

    mockPremiumServer.expectUserUpdatedRespondsWithError(user, {
      error: 'SOME_ERROR',
      detail: 'Some error text',
    })

    const modal = await ui.changeFullName('some terrible value')

    await flushPromises()

    expect(ui.getErrorText(modal)).toBe(
      "The action couldn't be completed because an unknown error has occured."
    )
  })

  test('a users full name cant be changed to less than 2 characters', async () => {
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const tooShortFullName = '1'

    const modal = await ui.changeFullName(tooShortFullName)
    const error = ui.getModalFieldErrorText(modal)

    expect(error).toContain(
      'Please enter a valid full name, it must be longer than 2 letters and less than 30.'
    )
  })

  test('a users full name cant be changed to more than 30 characters', async () => {
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const tooLongFullName = '1'.repeat(31)

    const modal = await ui.changeFullName(tooLongFullName)
    const error = ui.getModalFieldErrorText(modal)

    expect(error).toContain(
      'Please enter a valid full name, it must be longer than 2 letters and less than 30.'
    )
  })

  test('a users username be changed', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      username: 'oldusername@example.com',
    })

    const newUserName = 'new_email@example.com'
    mockPremiumServer.expectUserUpdated(user, {
      username: newUserName,
      // Expect the other edit modal fields will be sent, just with no changes.
      name: user.name,
      is_staff: user.is_staff,
      is_active: user.is_active,
    })

    await ui.changeEmail(newUserName)

    await flushPromises()

    const cells = ui.findCells()
    const { usernameCell } = ui.getRow(cells, 0)
    expect(usernameCell.text()).toContain(newUserName)
  })

  test('a users username cannot be changed to a invalid email address', async () => {
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    const invalidEmail = '1'

    const modal = await ui.changeEmail(invalidEmail)
    const error = ui.getModalFieldErrorText(modal)

    expect(error).toContain('Please enter a valid e-mail address.')
  })

  test('changing a users username and closing without saving resets the modals form', async () => {
    const initialUsername = 'initial_username@gmail.com'
    const { ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      username: initialUsername,
    })

    const usernameEnteredButNotSaved = '1'

    await ui.changeEmail(usernameEnteredButNotSaved, {
      clickSave: false,
      exit: true,
    })
    await flushPromises()
    const emailField = await ui.getUserEditModalEmailField()

    expect(emailField.element.value).toBe(initialUsername)
  })
  test('a user can be set as staff ', async () => {
    await testToggleStaff(false)
  })

  test('a user can be unset as staff ', async () => {
    await testToggleStaff(true)
  })

  test('a user can be set as active ', async () => {
    await testToggleActive(false)
  })

  test('a user can be unset as active', async () => {
    await testToggleActive(true)
  })

  test('when there are fewer than 100 users the page buttons do nothing', async () => {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin()

    await ui.clickNextPage()
    await ui.clickNextPage()
    await ui.clickPrevPage()

    await flushPromises()

    expect(ui.getSingleRowUsernameText()).toContain(user.username)
  })

  test('when there are 2 pages of users the next and back buttons switch between them', async () => {
    const firstPageUser = mockPremiumServer.aUser({
      username: 'firstPageUser@example.com',
    })
    const secondPageUser = mockPremiumServer.aUser({
      username: 'secondPageUser@example.com',
    })
    mockPremiumServer.thereAreUsers([firstPageUser], 1, { count: 150 })
    mockPremiumServer.thereAreUsers([secondPageUser], 2, { count: 150 })

    const userAdmin = await testApp.mount(UserAdminTable, {})
    const ui = new UserAdminUserHelpers(userAdmin)

    expect(ui.getSingleRowUsernameText()).toContain(firstPageUser.username)

    await ui.clickNextPage()
    await flushPromises()

    expect(ui.getSingleRowUsernameText()).toContain(secondPageUser.username)

    await ui.clickPrevPage()
    await flushPromises()

    expect(ui.getSingleRowUsernameText()).toContain(firstPageUser.username)
  })

  test('when not on the first page a sort will send the user back to the first page', async () => {
    const firstPageUser = mockPremiumServer.aUser({
      username: 'firstPageUser@example.com',
    })
    const secondPageUser = mockPremiumServer.aUser({
      username: 'secondPageUser@example.com',
    })
    mockPremiumServer.thereAreUsers([firstPageUser], 1, { count: 150 })
    mockPremiumServer.thereAreUsers([firstPageUser], 1, {
      count: 150,
      sorts: '+username',
    })
    mockPremiumServer.thereAreUsers([secondPageUser], 2, { count: 150 })

    const userAdmin = await testApp.mount(UserAdminTable, {})
    const ui = new UserAdminUserHelpers(userAdmin)

    expect(ui.getSingleRowUsernameText()).toContain(firstPageUser.username)

    await ui.clickNextPage()
    await ui.clickUsernameHeader()

    expect(ui.getSingleRowUsernameText()).toContain(firstPageUser.username)
  })

  test('you can search by username which will pass the search text to the server', async () => {
    const firstUser = mockPremiumServer.aUser({
      id: 1,
      username: 'firstUser@example.com',
    })
    const secondUser = mockPremiumServer.aUser({
      id: 2,
      username: 'secondUser@example.com',
    })
    mockPremiumServer.thereAreUsers([firstUser, secondUser], 1)
    mockPremiumServer.thereAreUsers([firstUser], 1, { search: 'firstUser' })

    const userAdmin = await testApp.mount(UserAdminTable, {})
    const ui = new UserAdminUserHelpers(userAdmin)

    const cells = ui.findCells(14)
    const { usernameCell: firstUsernameCell } = ui.getRow(cells, 0)
    expect(firstUsernameCell.text()).toContain('firstUser@example.com')
    const { usernameCell: secondUsernameCell } = ui.getRow(cells, 1)
    expect(secondUsernameCell.text()).toContain('secondUser@example.com')

    await ui.typeIntoSearchBox('firstUser')
    await flushPromises()

    expect(ui.getSingleRowUsernameText()).toContain(firstUser.username)
  })

  test('searching and then sorting will preserve the search', async () => {
    const firstUser = mockPremiumServer.aUser({
      id: 1,
      username: 'firstUser@example.com',
    })
    const secondUser = mockPremiumServer.aUser({
      id: 2,
      username: 'secondUser@example.com',
    })
    mockPremiumServer.thereAreUsers([firstUser, secondUser], 1)
    mockPremiumServer.thereAreUsers([firstUser], 1, { search: 'firstUser' })
    mockPremiumServer.thereAreUsers([firstUser], 1, {
      search: 'firstUser',
      sorts: '+username',
    })

    const userAdmin = await testApp.mount(UserAdminTable, {})
    const ui = new UserAdminUserHelpers(userAdmin)

    const cells = ui.findCells(14)
    const { usernameCell: firstUsernameCell } = ui.getRow(cells, 0)
    expect(firstUsernameCell.text()).toContain('firstUser@example.com')
    const { usernameCell: secondUsernameCell } = ui.getRow(cells, 1)
    expect(secondUsernameCell.text()).toContain('secondUser@example.com')

    await ui.typeIntoSearchBox('firstUser')
    await flushPromises()

    expect(ui.getSingleRowUsernameText()).toContain(firstUser.username)

    await ui.clickUsernameHeader()
    await flushPromises()

    expect(ui.getSingleRowUsernameText()).toContain(firstUser.username)
  })

  test('you can sort by multiple columns which will pass the sorts to the server', async () => {
    const first = 'firstUser@example.com'
    const second = 'secondUser@example.com'
    const third = 'thirdUser@example.com'
    const firstUser = mockPremiumServer.aUser({
      id: 1,
      username: first,
    })
    const secondUser = mockPremiumServer.aUser({
      id: 2,
      username: second,
    })
    const thirdUser = mockPremiumServer.aUser({
      id: 3,
      username: third,
    })
    mockPremiumServer.thereAreUsers([firstUser, secondUser, thirdUser], 1)

    const userAdmin = await testApp.mount(UserAdminTable, {})
    const ui = new UserAdminUserHelpers(userAdmin)

    let usernameCellsText = ui.findUsernameColumnCellsText()
    expect(usernameCellsText).toStrictEqual([first, second, third])

    // Clicking once starts with a descending sort
    mockPremiumServer.thereAreUsers([secondUser, firstUser, thirdUser], 1, {
      sorts: '+username',
    })
    await ui.clickUsernameHeader()
    await flushPromises()
    usernameCellsText = ui.findUsernameColumnCellsText()
    expect(usernameCellsText).toStrictEqual([second, first, third])

    // Clicking again toggles to a ascending sort
    mockPremiumServer.thereAreUsers([thirdUser, firstUser, secondUser], 1, {
      sorts: '-username',
    })
    await ui.clickUsernameHeader()
    await flushPromises()
    usernameCellsText = ui.findUsernameColumnCellsText()
    expect(usernameCellsText).toStrictEqual([third, first, second])

    // Clicking again turns off the sort
    await ui.clickUsernameHeader()
    await flushPromises()
    usernameCellsText = ui.findUsernameColumnCellsText()
    expect(usernameCellsText).toStrictEqual([first, second, third])

    // Can click multiple columns resulting in an ordered sort
    mockPremiumServer.thereAreUsers([firstUser, thirdUser, secondUser], 1, {
      sorts: '-username,+name',
    })
    await ui.clickUsernameHeader()
    await ui.clickUsernameHeader()
    await ui.clickFullnameHeader()
    await flushPromises()
    usernameCellsText = ui.findUsernameColumnCellsText()
    expect(usernameCellsText).toStrictEqual([first, third, second])
  })

  async function testToggleStaff(startingIsStaff) {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      isStaff: startingIsStaff,
    })

    let cells = ui.findCells()
    const { usernameCell } = ui.getRow(cells, 0)
    expect(ui.usernameCellIsForStaffMember(usernameCell)).toBe(startingIsStaff)

    mockPremiumServer.expectUserUpdated(user, {
      is_staff: !startingIsStaff,
      // Expect the other edit modal fields will be sent, just with no changes.
      username: user.username,
      name: user.name,
      is_active: user.is_active,
    })

    await ui.toggleIsStaff()

    await flushPromises()

    cells = ui.findCells()
    const { usernameCell: updatedUsernameCell } = ui.getRow(cells, 0)
    expect(ui.usernameCellIsForStaffMember(updatedUsernameCell)).toBe(
      !startingIsStaff
    )
  }

  async function testToggleActive(startingIsActive) {
    const { user, ui } = await whenThereIsAUserAndYouOpenUserAdmin({
      isActive: startingIsActive,
    })

    let cells = ui.findCells()
    const { isActiveCell } = ui.getRow(cells, 0)
    expect(isActiveCell.text()).toBe(
      startingIsActive ? 'Active' : 'Deactivated'
    )

    mockPremiumServer.expectUserUpdated(user, {
      is_active: !startingIsActive,
      // Expect the other edit modal fields will be sent, just with no changes.
      username: user.username,
      name: user.name,
      is_staff: user.is_staff,
    })

    await ui.toggleIsActive()

    await flushPromises()

    cells = ui.findCells()
    const { isActiveCell: updatedIsActiveCell } = ui.getRow(cells, 0)
    expect(updatedIsActiveCell.text()).toBe(
      startingIsActive ? 'Deactivated' : 'Active'
    )
  }

  async function whenThereIsAUserAndYouOpenUserAdmin(userSetup = {}) {
    const user = mockPremiumServer.aUser(userSetup)
    mockPremiumServer.thereAreUsers([user], 1)

    const userAdmin = await testApp.mount(UserAdminTable, {})
    const ui = new UserAdminUserHelpers(userAdmin)
    return { user, userAdmin, ui }
  }
})
