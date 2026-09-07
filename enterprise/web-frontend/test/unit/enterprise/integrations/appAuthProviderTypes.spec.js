import {
  SamlAppAuthProviderType,
  OpenIdConnectAppAuthProviderType,
} from '@baserow_enterprise/integrations/appAuthProviderTypes'

describe.each([
  [SamlAppAuthProviderType, 'saml'],
  [OpenIdConnectAppAuthProviderType, 'oidc'],
])('%s callback extraction', (Provider, protocol) => {
  test.each([undefined, null, '', ['one', 'two']])(
    'ignores missing or ambiguous credentials: %s',
    (value) => {
      expect(
        new Provider().getAuthToken(
          { id: 42 },
          {},
          {
            query: { [`user_source_${protocol}_token__42`]: value },
          }
        )
      ).toBeNull()
    }
  )

  test('extracts its user source token without browser access or route mutation', () => {
    const route = Object.freeze({
      query: Object.freeze({
        [`user_source_${protocol}_token__42`]: 'test-refresh-token',
        [`user_source_${protocol}_token__99`]: 'other-test-token',
      }),
    })
    vi.stubGlobal('window', undefined)
    try {
      expect(new Provider().getAuthToken({ id: 42 }, {}, route)).toBe(
        'test-refresh-token'
      )
    } finally {
      vi.unstubAllGlobals()
    }
  })
})
