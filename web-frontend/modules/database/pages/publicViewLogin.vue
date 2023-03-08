<template>
  <div>
    <div class="box__head">
      <h2 class="box__head-title">{{ $t('publicViewAuthLogin.title') }}</h2>
    </div>
    <div>
      <Error :error="error"></Error>
      <form @submit.prevent="authorizeView">
        <p class="box__description">
          {{ $t('publicViewAuthLogin.description') }}
        </p>
        <FormElement :error="fieldHasErrors('password')" class="control">
          <div class="control__elements">
            <input
              ref="password"
              v-model="values.password"
              :class="{ 'input--error': fieldHasErrors('password') }"
              type="password"
              class="input input--large"
            />
            <div v-if="fieldHasErrors('password')" class="error">
              {{ $t('error.passwordRequired') }}
            </div>
          </div>
        </FormElement>
        <div class="public-view-auth__actions">
          <button
            class="button button--large button--primary"
            :class="{ 'button--loading': loading }"
            :disabled="loading || $v.$invalid"
          >
            {{ $t('publicViewAuthLogin.enter') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import error from '@baserow/modules/core/mixins/error'
import { required } from 'vuelidate/lib/validators'
import { mapActions } from 'vuex'
import { isRelativeUrl } from '@baserow/modules/core/utils/url'
import languageDetection from '@baserow/modules/core/mixins/languageDetection'

export default {
  mixins: [form, error, languageDetection],
  layout: 'login',
  data() {
    return {
      loading: false,
      allowedValues: ['password'],
      values: {
        password: '',
      },
    }
  },
  head() {
    return {
      title: 'Password protected view',
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.$refs.password.focus()
    })
  },
  methods: {
    clearInput() {
      this.values.password = ''
    },
    async authorizeView() {
      this.hideError()
      this.loading = true

      try {
        const slug = this.$route.params.slug
        const rsp = await this.$client.post(
          `/database/views/${slug}/public/auth/`,
          { password: this.values.password }
        )
        await this.setPublicAuthToken({ slug, token: rsp.data.access_token })

        // Redirect to the original view.
        // Subsequent requests will use the token saved into the store.
        const { original } = this.$route.query
        if (original && isRelativeUrl(original)) {
          await this.$router.push(original)
        }
      } catch (e) {
        const statusCode = e.response?.status
        // hide the authorization error here and show the correct error message
        if (statusCode === 401) {
          this.$store.dispatch('notification/setAuthorizationError', false)
          this.showError(
            this.$t('publicViewAuthLogin.error.incorrectPasswordTitle'),
            this.$t('publicViewAuthLogin.error.incorrectPasswordText')
          )
        } else {
          this.handleError(e, 'auth')
        }
        this.loading = false
      }
    },
    ...mapActions({
      setPublicAuthToken: 'page/view/public/setAuthToken',
    }),
  },
  validations: {
    values: {
      password: { required },
    },
  },
}
</script>
