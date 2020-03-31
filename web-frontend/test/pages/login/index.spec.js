import createNuxt from '@/test/helpers/create-nuxt'

let nuxt = null

describe('children', () => {
  beforeAll(async (done) => {
    nuxt = await createNuxt(true)
    done()
  }, 120000)

  test('/login', async () => {
    const { html } = await nuxt.server.renderRoute('/login')
    expect(html).toContain('Login')
  })

  afterAll(async () => {
    await nuxt.close()
  })
})
