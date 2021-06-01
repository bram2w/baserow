<template>
  <div>
    <div v-if="exporterTypes.length > 0" class="control">
      <label class="control__label"
        >To which format would you like to export?</label
      >
      <div class="control__elements">
        <ul class="choice-items">
          <li v-for="exporterType in exporterTypes" :key="exporterType.type">
            <a
              class="choice-items__link"
              :class="{
                active: value !== null && value === exporterType.type,
                disabled: loading,
              }"
              @click="switchToExporterType(exporterType.type)"
            >
              <i
                class="choice-items__icon fas"
                :class="'fa-' + exporterType.iconClass"
              ></i>
              {{ exporterType.name }}
            </a>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    exporterTypes: {
      required: true,
      type: Array,
    },
    value: {
      required: false,
      type: String,
      default: null,
    },
    loading: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    switchToExporterType(exporterType) {
      if (this.loading) {
        return
      }

      this.$emit('input', exporterType)
    },
  },
}
</script>
