<template>
  <Modal
    left-sidebar
    left-sidebar-scrollable
    :content-padding="
      settingSelected == null ? true : settingSelected.componentPadding
    "
  >
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
            <i class="modal-sidebar__nav-icon" :class="setting.icon"></i>
            {{ setting.name }}
          </a>
        </li>
      </ul>
    </template>
    <template v-if="settingSelected" #content>
      <component :is="settingSelected.component" :builder="builder"></component>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import { BuilderApplicationType } from '@baserow/modules/builder/applicationTypes'

export default {
  name: 'BuilderSettingsModal',
  mixins: [modal],
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
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
    show(...args) {
      if (!this.settingSelected) {
        this.settingSelected = this.registeredSettings[0]
      }

      const builderApplicationType = this.$registry.get(
        'application',
        BuilderApplicationType.getType()
      )
      builderApplicationType.loadExtraData(this.builder)

      return modal.methods.show.call(this, ...args)
    },
  },
}
</script>
