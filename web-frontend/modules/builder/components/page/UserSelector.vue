<template>
  <div class="inline-block">
    <a
      ref="button_user_source_users"
      class="header__filter-link"
      @click="
        $refs['user_source_users_context'].toggle(
          $refs['button_user_source_users'],
          'bottom',
          'left',
          4
        )
      "
    >
      <i class="header__filter-icon iconoir-user"></i>
      <span class="header__filter-name">
        {{
          $t('userSelector.viewAs', {
            user: isAuthenticated
              ? loggedUser.username
              : $t('userSelector.anonymous'),
          })
        }}
        {{ userRole }}
      </span>
    </a>
    <UserSourceUsersContext ref="user_source_users_context" />
  </div>
</template>

<script>
import UserSourceUsersContext from '@baserow/modules/builder/components/page/UserSourceUsersContext'
import { DEFAULT_USER_ROLE_PREFIX } from '@baserow/modules/builder/constants'

export default {
  components: { UserSourceUsersContext },
  inject: ['builder'],
  props: {},
  computed: {
    isAuthenticated() {
      return this.$store.getters['userSourceUser/isAuthenticated'](this.builder)
    },
    loggedUser() {
      return this.$store.getters['userSourceUser/getUser'](this.builder)
    },
    userSourceName() {
      return this.$store.getters['userSource/getUserSourceById'](
        this.builder,
        this.loggedUser.user_source_id
      ).name
    },
    userRole() {
      if (!this.isAuthenticated) {
        return ''
      }
      if (this.loggedUser.role.startsWith(DEFAULT_USER_ROLE_PREFIX)) {
        return (
          '- ' +
          this.$t('userSelector.member', {
            prefix: this.userSourceName,
          })
        )
      } else if (!this.loggedUser.role.trim().length) {
        return `- ${this.$t('visibilityForm.noRole')}`
      } else {
        return `- ${this.loggedUser.role}`
      }
    },
  },
}
</script>
