<template>
  <div>
    <h1 class="box__title">REST API</h1>
    <template v-if="isAuthenticated">
      <p>
        After you have created your database schema and API key in the
        <a @click.prevent="$refs.settingsModal.show('tokens')">settings</a>,
        your Baserow database provides his own REST API endpoints to create,
        read, update and delete rows.
      </p>
      <div class="select-application__title">
        For which database do you want to see the documentation?
      </div>
      <APIDocsSelectDatabase></APIDocsSelectDatabase>
      <SettingsModal ref="settingsModal"></SettingsModal>
    </template>
    <template v-else>
      <p>
        After you have created your database schema and API key in the settings,
        your Baserow database provides his own REST API endpoints to create,
        read, update and delete rows.
      </p>
      <nuxt-link
        :to="{
          name: 'login',
          query: {
            original: $route.path,
          },
        }"
        class="button button--ghost button--large"
        >Sign in to get started</nuxt-link
      >
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import SettingsModal from '@baserow/modules/core/components/settings/SettingsModal'
import APIDocsSelectDatabase from '@baserow/modules/database/components/docs/APIDocsSelectDatabase'

export default {
  name: 'APIDocs',
  components: { SettingsModal, APIDocsSelectDatabase },
  layout: 'login',
  middleware: ['groupsAndApplications'],
  head() {
    return {
      title: 'REST API documentation',
    }
  },
  computed: {
    ...mapGetters({
      isAuthenticated: 'auth/isAuthenticated',
    }),
  },
}
</script>
