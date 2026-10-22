import { afterEach, beforeEach, describe, expect, test } from 'vitest'

import { TestApp } from '@baserow/test/helpers/testApp'
import ApplicationSelector from '@baserow/modules/core/components/export/ApplicationSelector'

describe('ApplicationSelector', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountComponent = (props = {}) =>
    testApp.mount(ApplicationSelector, {
      props: { workspace: { id: 1 }, ...props },
    })

  test('shows the export title by default', async () => {
    const wrapper = await mountComponent()

    expect(wrapper.find('.application-selector__title').text()).toBe(
      'exportWorkspaceForm.selectDataToExport'
    )
  })

  test('shows the given title', async () => {
    const wrapper = await mountComponent({ title: 'Content' })

    expect(wrapper.find('.application-selector__title').text()).toBe('Content')
  })
})
