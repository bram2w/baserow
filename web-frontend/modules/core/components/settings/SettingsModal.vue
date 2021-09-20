<template>
  <Modal :left-sidebar="true" :left-sidebar-scrollable="true">
    <template #sidebar>
      <div class="modal-sidebar__head">
        <div class="modal-sidebar__head-initials-icon">
          {{ name | nameAbbreviation }}
        </div>
        <div class="modal-sidebar__head-name">
          {{ $t('settingsModal.title') }}
        </div>
      </div>
      <ul class="modal-sidebar__nav">
        <li v-for="setting in registeredSettings" :key="setting.type">
          <a
            class="modal-sidebar__nav-link"
            :class="{ active: page === setting.type }"
            @click="setPage(setting.type)"
          >
            <i
              class="fas modal-sidebar__nav-icon"
              :class="'fa-' + setting.iconClass"
            ></i>
            {{ setting.getName() }}
          </a>
        </li>
      </ul>
    </template>
    <template #content>
      <component :is="settingPageComponent"></component>
    </template>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'

import PasswordSettings from '@baserow/modules/core/components/settings/PasswordSettings'

export default {
  name: 'SettingsModal',
  components: { PasswordSettings },
  mixins: [modal],
  data() {
    return {
      page: null,
    }
  },
  computed: {
    registeredSettings() {
      return this.$registry.getAll('settings')
    },
    settingPageComponent() {
      const active = Object.values(this.$registry.getAll('settings')).find(
        (setting) => setting.type === this.page
      )
      return active ? active.getComponent() : null
    },
    ...mapGetters({
      name: 'auth/getName',
    }),
  },
  methods: {
    setPage(page) {
      this.page = page
    },
    isPage(page) {
      return this.page === page
    },
    show(page, ...args) {
      this.page = page
      return modal.methods.show.call(this, ...args)
    },
  },
}
</script>

<i18n>
{
  "en": {
    "settingsModal": {
      "title": "Settings"
    }
  },
  "fr": {
    "settingsModal": {
      "title": "Profil"
    }
  }
}
</i18n>
