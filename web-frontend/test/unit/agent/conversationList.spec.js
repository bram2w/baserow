import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { TestApp } from '@baserow/test/helpers/testApp'
import AgentConversationList from '@baserow/modules/agent/components/AgentConversationList'

describe('Agent conversation list', () => {
  let testApp, form

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
    form?.remove()
    form = null
  })

  test('activates conversations and shared actions without submitting an enclosing form', async () => {
    const conversation = { uuid: 'saved', title: 'Saved conversation' }
    const wrapper = await testApp.mount(AgentConversationList, {
      props: {
        items: [conversation],
        hasMore: true,
        canCreate: true,
        readyToSend: true,
      },
    })
    form = document.createElement('form')
    const submit = vi.fn((event) => event.preventDefault())
    form.addEventListener('submit', submit)
    document.body.appendChild(form)
    form.appendChild(wrapper.element)

    wrapper.get('.agent-conversations__item').element.click()
    wrapper.get('.agent-conversations__more').element.click()
    wrapper.get('.agent-conversations__footer button').element.click()
    await wrapper.setProps({ error: true })
    wrapper.get('.alert button').element.click()

    expect(submit).not.toHaveBeenCalled()
    expect(wrapper.emitted('select')).toEqual([[conversation]])
    for (const action of ['load-more', 'create', 'retry']) {
      expect(wrapper.emitted(action)).toHaveLength(1)
    }
  })

  test('retains focus and selection while existing rows load or reorder', async () => {
    const saved = { uuid: 'saved', title: 'Saved conversation' }
    const draft = { uuid: 'draft', title: '', local: true }
    const wrapper = await testApp.mount(AgentConversationList, {
      props: { items: [saved, draft], selected: 'saved', hasMore: true },
    })
    const selected = wrapper.get('[aria-current="true"]')
    selected.element.focus()

    await wrapper.setProps({ loading: true, items: [draft, saved] })
    const more = wrapper.get('.agent-conversations__more')
    more.element.click()

    expect(wrapper.get('[aria-current="true"]').element).toBe(selected.element)
    expect(document.activeElement).toBe(selected.element)
    expect(wrapper.findAll('li')).toHaveLength(2)
    expect(wrapper.get('.agent-conversations__draft').text()).toBe(
      'agent.draft'
    )
    expect(wrapper.find('.skeleton').exists()).toBe(false)
    expect(more.element.disabled).toBe(true)
    expect(wrapper.emitted('load-more')).toBeUndefined()
  })
})
