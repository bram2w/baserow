<template>
  <div class="sidebar__impersonate">
    <div v-if="impersonating" class="impersonate-warning">
      {{ $t('premiumTopSidebar.impersonateDescription') }}
      <div>
        <Button
          class="margin-top-1"
          type="danger"
          tag="a"
          size="small"
          :href="resolveAdminUsersHref()"
          :loading="loading"
          :disabled="loading"
          @click="loading = true"
          >{{ $t('premiumTopSidebar.impersonateStop') }}</Button
        >
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'Impersonate',
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
