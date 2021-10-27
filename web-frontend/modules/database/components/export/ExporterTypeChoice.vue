<template>
  <li>
    <a
      v-tooltip="deactivated ? deactivatedText : null"
      class="choice-items__link"
      :class="{ active, disabled, deactivated }"
      @click="select(exporterType)"
    >
      <i
        class="choice-items__icon fas"
        :class="'fa-' + exporterType.iconClass"
      ></i>
      {{ exporterType.getName() }}
    </a>
  </li>
</template>

<script>
export default {
  name: 'ExporterTypeChoice',
  props: {
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
        .isDeactivated()
    },
  },
  methods: {
    select(exporterType) {
      if (this.disabled || this.deactivated) {
        return
      }

      this.$emit('selected', exporterType)
    },
  },
}
</script>
