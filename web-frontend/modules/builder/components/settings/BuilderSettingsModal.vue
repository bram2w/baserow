<template>
  <Modal left-sidebar left-sidebar-scrollable>
    <template #sidebar>
      <div class="modal-sidebar__head">
        <div class="modal-sidebar__head-name">
          {{ $t('builderSettingsModal.title') }}
        </div>
      </div>
      <ul class="modal-sidebar__nav">
        <li v-for="setting in registeredSettings" :key="setting.getType()">
          <a
            class="modal-sidebar__nav-link"
            :class="{ active: setting === settingSelected }"
            @click="settingSelected = setting"
          >
            <i
              class="fas modal-sidebar__nav-icon"
              :class="'fa-' + setting.getIconClass()"
            ></i>
            {{ setting.getName() }}
          </a>
        </li>
      </ul>
    </template>
    <template v-if="settingSelected" #content>
      <component :is="settingSelected.getComponent()"></component>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'BuilderSettingsModal',
  mixins: [modal],
  data() {
    return {
      settingSelected: null,
    }
  },
  computed: {
    registeredSettings() {
      return this.$registry.getOrderedList('builderSettings')
    },
  },
  methods: {
    setPage(page) {
      this.page = page
    },
    show(...args) {
      if (!this.settingSelected) {
        this.settingSelected = this.registeredSettings[0]
      }
      return modal.methods.show.call(this, ...args)
    },
  },
}
</script>
