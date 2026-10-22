import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, test, vi } from 'vitest'

import GeneralSettings from '@baserow/modules/automation/components/settings/GeneralSettings'

describe('Automation General settings', () => {
  test('lets an editor explicitly enable imported custom code', async () => {
    const automation = {
      id: 10,
      name: 'Imported automation',
      notification: false,
      untrusted_content: true,
    }
    const dispatch = vi.fn().mockResolvedValue(undefined)
    const wrapper = await mountSuspended(GeneralSettings, {
      props: { automation, defaultValues: automation },
      global: {
        mocks: { $store: { dispatch } },
      },
    })
    await flushPromises()

    const restriction = wrapper
      .findAllComponents({ name: 'Checkbox' })
      .find((checkbox) =>
        checkbox.text().includes('generalSettings.blockUntrustedContent')
      )
    expect(restriction.html()).toMatchSnapshot()
    await restriction.find('input').setValue(false)
    await flushPromises()

    expect(dispatch).toHaveBeenCalledWith('application/update', {
      application: automation,
      values: {
        name: 'Imported automation',
        notification: false,
        untrusted_content: false,
      },
    })
  })
})
