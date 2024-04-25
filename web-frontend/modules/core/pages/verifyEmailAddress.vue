<script>
import AuthService from '@baserow/modules/core/services/auth'

export default {
  async asyncData({ store, params, error, app, redirect }) {
    const { token } = params

    try {
      await AuthService(app.$client).verifyEmail(token)
    } catch {
      return error({
        statusCode: 404,
        message: 'Not a valid confirmation token.',
      })
    }

    return redirect({ name: 'login', query: { emailVerified: true } })
  },
}
</script>
