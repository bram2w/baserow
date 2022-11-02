<template>
  <div>
    <div class="layout__col-2-1">
      <ul class="page-tabs">
        <nuxt-link
          v-slot="{ href, navigate, isExactActive }"
          :to="{
            name: 'settings-members',
            params: {
              groupId: group.id,
            },
          }"
        >
          <li
            class="page-tabs__item"
            :class="{ 'page-tabs__item--active': isExactActive }"
          >
            <a :href="href" class="page-tabs__link" @click="navigate">
              {{ $t('membersSettings.membersTabTitle') }}
            </a>
          </li>
        </nuxt-link>
        <nuxt-link
          v-if="$hasPermission('group.list_invitations', group, group.id)"
          v-slot="{ href, navigate, isExactActive }"
          :to="{
            name: 'settings-invites',
            params: {
              groupId: group.id,
            },
          }"
        >
          <li
            class="page-tabs__item"
            :class="{ 'page-tabs__item--active': isExactActive }"
          >
            <a :href="href" class="page-tabs__link" @click="navigate">
              {{ $t('membersSettings.invitesTabTitle') }}
            </a>
          </li>
        </nuxt-link>
      </ul>
    </div>
    <div class="layout__col-2-2">
      <NuxtChild :group="group" />
    </div>
  </div>
</template>
store/roles.js

<script>
export default {
  name: 'Settings',
  layout: 'app',
  async asyncData({ store, params, error }) {
    try {
      const group = await store.dispatch(
        'group/selectById',
        parseInt(params.groupId, 10)
      )
      return { group }
    } catch (e) {
      return error({ statusCode: 404, message: 'Group not found.' })
    }
  },
  mounted() {
    this.$bus.$on('group-deleted', this.groupDeleted)
  },
  beforeDestroy() {
    this.$bus.$off('group-deleted', this.groupDeleted)
  },
  methods: {
    groupDeleted() {
      this.$nuxt.$router.push({ name: 'dashboard' })
    },
  },
}
</script>
