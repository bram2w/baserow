<template>
  <Modal :sidebar="true">
    <template v-slot:sidebar>
      <div class="settings__head">
        <div class="settings__head-icon">{{ nameAbbreviation }}</div>
        <div class="settings__head-name">Settings</div>
      </div>
      <ul class="settings__nav">
        <li>
          <a
            class="settings__nav-link"
            :class="{ active: page === 'password' }"
            @click="setPage('password')"
          >
            <i class="fas fa-lock settings__nav-icon"></i>
            Password
          </a>
        </li>
      </ul>
    </template>
    <template v-slot:content>
      <PasswordSettings v-if="isPage('password')"></PasswordSettings>
    </template>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'

import PasswordSettings from '@baserow/modules/core/components/settings/PasswordSettings'

export default {
  name: 'AccountModal',
  components: { PasswordSettings },
  mixins: [modal],
  data() {
    return {
      page: null,
    }
  },
  computed: {
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
