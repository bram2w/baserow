<template>
  <div>
    <h1 class="box__title">Sign up</h1>
    <template v-if="!settings.allow_new_signups">
      <div class="alert alert--simple alert--error alert--has-icon">
        <div class="alert__icon">
          <i class="fas fa-exclamation"></i>
        </div>
        <div class="alert__title">Sign up is disabled</div>
        <p class="alert__content">
          It's not possible to create an account because it has been disabled.
        </p>
      </div>
      <nuxt-link
        :to="{ name: 'login' }"
        class="button button--large button--primary"
      >
        <i class="fas fa-arrow-left"></i>
        Back to login
      </nuxt-link>
    </template>
    <AuthRegister v-else :invitation="invitation" @success="success">
      <ul class="action__links">
        <li>
          <nuxt-link :to="{ name: 'login' }">
            <i class="fas fa-arrow-left"></i>
            Back
          </nuxt-link>
        </li>
      </ul>
    </AuthRegister>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'
import AuthRegister from '@baserow/modules/core/components/auth/AuthRegister'

export default {
  components: { AuthRegister },
  mixins: [groupInvitationToken],
  layout: 'login',
  head() {
    return {
      title: 'Create new account',
    }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  methods: {
    success() {
      this.$nuxt.$router.push({ name: 'dashboard' })
    },
  },
}
</script>
