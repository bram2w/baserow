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
import { mapActions } from 'vuex'

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
    userSource() {
      return this.$store.getters['userSource/getUserSourceByUId'](
        this.builder,
        this.loggedUser.user_source_uid
      )
    },
    userRole() {
      if (!this.isAuthenticated) {
        return ''
      }

      if (
        this.userSource &&
        this.loggedUser.role.startsWith(DEFAULT_USER_ROLE_PREFIX)
      ) {
        return (
          '- ' +
          this.$t('userSelector.member', {
            prefix: this.userSource.name,
          })
        )
      } else if (!this.loggedUser.role.trim().length) {
        return `- ${this.$t('visibilityForm.noRole')}`
      } else {
        return `- ${this.loggedUser.role}`
      }
    },
  },
  watch: {
    /**
     * When the User Source is deleted, log off the currently selected user.
     */
    userSource(newValue, oldValue) {
      if (!newValue && this.isAuthenticated) {
        this.actionLogoff({ application: this.builder })
      }
    },
  },
  methods: {
    ...mapActions({
      actionLogoff: 'userSourceUser/logoff',
    }),
  },
}
</script>
