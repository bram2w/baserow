import oauth2Result from '@baserow/modules/integrations/oauth2/plugins/oauth2Result'
import {
  getOAuth2Flow,
  startOAuth2Flow,
} from '@baserow/modules/integrations/oauth2/utils/flow'

function runPlugin(search) {
  window.history.replaceState(null, '', `/automation/1${search}`)
  const dispatch = vi.fn()
  let mounted = null
  oauth2Result({
    hook: (name, callback) => {
      if (name === 'app:mounted') {
        mounted = callback
      }
    },
    $store: { dispatch },
    $i18n: { t: (key) => key },
  })
  mounted()
  return dispatch
}

describe('oauth2Result plugin', () => {
  afterEach(() => {
    window.sessionStorage.clear()
  })

  test('shows the outcome of a flow this tab started', () => {
    startOAuth2Flow(1, 'http://localhost/automation/1')
    const dispatch = runPlugin('?oauth2_status=error&oauth2_error=Bad%20code')

    expect(dispatch).toHaveBeenCalledWith('toast/error', {
      title: 'oauth2Result.errorTitle',
      message: 'Bad code',
    })
    expect(window.location.search).toBe('')
    expect(getOAuth2Flow()).toBeNull()
  })

  test('ignores an outcome from a link nobody started here', () => {
    const dispatch = runPlugin(
      '?oauth2_status=error&oauth2_error=Call%20this%20number&tab=x'
    )

    expect(dispatch).not.toHaveBeenCalled()
    expect(window.location.search).toBe('?tab=x')
  })
})
