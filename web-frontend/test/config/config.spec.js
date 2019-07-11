import createNuxt from '@/test/helpers/create-nuxt'

let nuxt = null

describe('Config', () => {
  beforeAll(async done => {
    nuxt = await createNuxt(true)
    done()
  }, 120000)

  test('Plugins', () => {
    const plugins = nuxt.options.plugins.map(option => option.src)
    expect(plugins.includes('@/plugins/auth.js')).toBe(true)
    expect(plugins.includes('@/plugins/vuelidate.js')).toBe(true)
  })

  afterAll(async () => {
    await nuxt.close()
  })
})
