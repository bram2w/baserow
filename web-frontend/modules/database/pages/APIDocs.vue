<template>
  <div>
    <h1 class="box__title">{{ $t('apiDocsComponent.title') }}</h1>
    <template v-if="isAuthenticated">
      <i18n path="apiDocs.intro" tag="p">
        <template #settingsLink>
          <a @click.prevent="$refs.settingsModal.show('tokens')">{{
            $t('apiDocsComponent.settings')
          }}</a
          >,
        </template>
      </i18n>
      <div class="select-application__title">
        {{ $t('apiDocsComponent.selectApplicationTitle') }}
      </div>
      <APIDocsSelectDatabase />
      <nuxt-link :to="{ name: 'dashboard' }" class="select-application__back">
        <i class="fas fa-arrow-left"></i>
        {{ $t('apiDocsComponent.back') }}
      </nuxt-link>
      <SettingsModal ref="settingsModal"></SettingsModal>
    </template>
    <template v-else>
      <i18n path="apiDocsComponent.intro" tag="p">
        <template #settingsLink>{{ $t('apiDocsComponent.settings') }},</template
        >,
      </i18n>
      <nuxt-link
        :to="{
          name: 'login',
          query: {
            original: $route.path,
          },
        }"
        class="button button--ghost button--large"
      >
        {{ $t('apiDocsComponent.signIn') }}
      </nuxt-link>
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
