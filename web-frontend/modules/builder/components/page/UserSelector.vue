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
      </span>
    </a>
    <UserSourceUsersContext ref="user_source_users_context" />
  </div>
</template>

<script>
import UserSourceUsersContext from '@baserow/modules/builder/components/page/UserSourceUsersContext'

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
  },
}
</script>
