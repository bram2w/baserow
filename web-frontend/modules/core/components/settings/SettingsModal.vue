<template>
  <Modal :sidebar="true">
    <template v-slot:sidebar>
      <div class="settings__head">
        <div class="settings__head-icon">{{ nameAbbreviation }}</div>
        <div class="settings__head-name">Settings</div>
      </div>
      <ul class="settings__nav">
        <li v-for="setting in registeredSettings" :key="setting.type">
          <a
            class="settings__nav-link"
            :class="{ active: page === setting.type }"
            @click="setPage(setting.type)"
          >
            <i
              class="fas settings__nav-icon"
              :class="'fa-' + setting.iconClass"
            ></i>
            {{ setting.name }}
          </a>
        </li>
      </ul>
    </template>
    <template v-slot:content>
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
      nameAbbreviation: 'auth/getNameAbbreviation',
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
