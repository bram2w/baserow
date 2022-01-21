import createNuxt from '@/test/helpers/create-nuxt'

let nuxt = null

describe('children', () => {
  beforeAll(async (done) => {
    nuxt = await createNuxt(true, 3503)
    done()
  }, 120000)

  test('/login', async () => {
    const { html } = await nuxt.server.renderRoute('/signup')
    expect(html).toContain('Sign up')
  })

  afterAll(async () => {
    await nuxt.close()
  })
})
