import WebhookForm from '@baserow/modules/database/components/webhook/WebhookForm'
import { TestApp } from '@baserow/test/helpers/testApp'

describe('Webhook form Input Tests', () => {
  let testApp = null

  beforeAll(() => {
    testApp = new TestApp()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  function mountWebhookForm() {
    return testApp.mount(WebhookForm, {
      propsData: {
        table: { id: 1 },
        database: { id: 2, workspace: { id: 3 } },
        fields: [{ id: 1, name: 'Name', type: 'text' }],
      },
    })
  }

  async function changeURL(wrapper, urlValue) {
    const urlInput = wrapper.find(
      'input[placeholder="webhookForm.inputLabels.url"]'
    )

    urlInput.element.value = urlValue
    await urlInput.trigger('input')
    await urlInput.trigger('blur')
  }

  function getErrorDivs(wrapper) {
    return wrapper.findAll('div > .control__messages--error')
  }

  function getErrorTexts(errorDivs) {
    return errorDivs.wrappers.map((w) =>
      w.text().replace(/\n/gm, '').replace(/\s\s+/g, ' ')
    )
  }

  test('WebhookForm displays an error on missing URL', async () => {
    const wrapper = await mountWebhookForm()
    await changeURL(wrapper, '')

    const errorDiv = getErrorDivs(wrapper)
    expect(errorDiv.exists()).toBe(true)
    expect(getErrorTexts(errorDiv)).toEqual(['webhookForm.errors.urlField'])
  })

  test('WebhookForm displays an error on too long URL', async () => {
    const wrapper = await mountWebhookForm()
    await changeURL(wrapper, 'http://google.de/' + 'a'.repeat(2001 - 16))

    const errorDiv = getErrorDivs(wrapper)
    expect(errorDiv.exists()).toBe(true)
    expect(getErrorTexts(errorDiv)).toEqual(['error.maxLength'])
  })

  test('WebhookForm displays an error on invalid URL', async () => {
    const wrapper = await mountWebhookForm()
    await changeURL(wrapper, 'htt://google.de')

    const errorDiv = getErrorDivs(wrapper)
    expect(errorDiv.exists()).toBe(true)
    expect(getErrorTexts(errorDiv)).toEqual(['webhookForm.errors.urlField'])
  })
})
