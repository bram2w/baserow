<template>
  <div v-if="impersonating" class="impersonate-warning">
    This account is impersonated. A page refresh will stop it.
    <div>
      <a
        :href="resolveAdminUsersHref()"
        class="button button--error button--tiny margin-top-1"
        :class="{ 'button--loading': loading }"
        @click="loading = true"
        >Stop</a
      >
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'IsImpersonating',
  data() {
    return {
      loading: false,
    }
  },
  computed: {
    ...mapGetters({
      impersonating: 'impersonating/getImpersonating',
    }),
  },
  methods: {
    resolveAdminUsersHref() {
      const props = this.$nuxt.$router.resolve({ name: 'admin-users' })
      return props.href
    },
  },
}
</script>
