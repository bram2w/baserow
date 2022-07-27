<template>
  <li>
    <a
      v-tooltip="deactivated ? deactivatedText : null"
      class="choice-items__link"
      :class="{ active, disabled }"
      @click="select(exporterType)"
    >
      <i
        class="choice-items__icon fas"
        :class="'fa-' + exporterType.iconClass"
      ></i>
      {{ exporterType.getName() }}
      <div v-if="deactivated" class="deactivated-label">
        <i class="fas fa-lock"></i>
      </div>
    </a>
    <component
      v-if="deactivatedClickModal !== null"
      :is="deactivatedClickModal"
      ref="deactivatedClickModal"
      :name="exporterType.getName()"
    ></component>
  </li>
</template>

<script>
export default {
  name: 'ExporterTypeChoice',
  props: {
    database: {
      type: Object,
      required: true,
    },
    exporterType: {
      required: true,
      type: Object,
    },
    active: {
      required: true,
      type: Boolean,
    },
    disabled: {
      required: true,
      type: Boolean,
    },
  },
  computed: {
    deactivatedText() {
      return this.$registry
        .get('exporter', this.exporterType.type)
        .getDeactivatedText()
    },
    deactivated() {
      return this.$registry
        .get('exporter', this.exporterType.type)
        .isDeactivated(this.database.group.id)
    },
    deactivatedClickModal() {
      return this.$registry
        .get('exporter', this.exporterType.type)
        .getDeactivatedClickModal()
    },
  },
  methods: {
    select(exporterType) {
      if (this.deactivated && this.deactivatedClickModal) {
        this.$refs.deactivatedClickModal.show()
      } else if (!this.disabled && !this.deactivated) {
        this.$emit('selected', exporterType)
      }
    },
  },
}
</script>
