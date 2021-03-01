import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'
import httpMocks from 'node-mocks-http'

import createNuxt from '@/test/helpers/create-nuxt'

let nuxt = null
let mock = null

describe('index redirect', () => {
  beforeAll(async (done) => {
    mock = new MockAdapter(axios)

    // Because the token 'test1' exists it will be refreshed immediately, the
    // refresh endpoint is stubbed so that it will always provide a valid
    // unexpired token.
    mock.onPost('http://localhost/api/user/token-refresh/').reply(200, {
      token:
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2' +
        'VybmFtZSI6InRlc3RAdGVzdCIsImV4cCI6MTk5OTk5OTk5OSwiZW1haWwiO' +
        'iJ0ZXN0QHRlc3QubmwiLCJvcmlnX2lhdCI6MTU2Mjc3MzQxNH0.2i0gqrcH' +
        '5uy7mk4kf3LoLpZYXoyMrOfi0fDQneVcaFE',
      user: {
        first_name: 'Test',
        username: 'test@test.nl',
      },
    })

    nuxt = await createNuxt(true)
    done()
  })

  test('if not authenticated', async () => {
    const { redirected } = await nuxt.server.renderRoute('/')
    expect(redirected.path).toBe('/login')
    expect(redirected.status).toBe(302)
  })

  test('if authenticated', async () => {
    const req = httpMocks.createRequest({
      headers: {
        cookie: 'jwt_token=test1',
      },
    })
    const res = httpMocks.createResponse()
    const { redirected } = await nuxt.server.renderRoute('/', { req, res })
    expect(redirected.path).toBe('/dashboard')
    expect(redirected.status).toBe(302)
  })

  afterAll(async () => {
    await nuxt.close()
  })
})
