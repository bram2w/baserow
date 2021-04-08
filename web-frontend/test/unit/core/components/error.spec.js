import Error from '@baserow/modules/core/components/Error'
import { bootstrapVueContext } from '@baserow/test/helpers/components'

describe('Error Component Tests', () => {
  let vueContext = null

  beforeEach(() => {
    vueContext = bootstrapVueContext()
  })

  afterEach(() => {
    vueContext.teardownVueContext()
  })

  function errorComponent(props) {
    return vueContext.vueTestUtils.shallowMount(Error, {
      localVue: vueContext.vue,
      propsData: props,
    })
  }

  test('When visible prop is true title and message are shown', () => {
    const error = errorComponent({
      error: {
        visible: true,
        title: 'TestError',
        message: 'message',
      },
    })

    const html = error.html()
    expect(html).toMatch('TestError')
    expect(html).toMatch('message')
  })

  test('When visible prop is false no html is rendered', () => {
    const error = errorComponent({
      error: {
        visible: false,
        title: 'TestError',
        message: 'message',
      },
    })

    expect(error.html()).toStrictEqual('')
  })
})
