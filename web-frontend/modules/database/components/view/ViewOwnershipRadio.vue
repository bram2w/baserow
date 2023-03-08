<template>
  <Radio
    v-tooltip="
      viewOwnershipType.isDeactivated()
        ? viewOwnershipType.getDeactivatedText()
        : null
    "
    :model-value="selectedType"
    :value="viewOwnershipType.getType()"
    @input="input"
  >
    <i :class="viewOwnershipType.getIconClass()"></i>
    {{ viewOwnershipType.getName() }}
    <div v-if="viewOwnershipType.isDeactivated()" class="deactivated-label">
      <i class="fas fa-lock"></i>
    </div>
    <component
      :is="viewOwnershipType.getDeactivatedModal()"
      v-if="viewOwnershipType.getDeactivatedModal() !== null"
      ref="deactivatedClickModal"
      :name="viewOwnershipType.getFeatureName()"
    ></component>
  </Radio>
</template>

<script>
import Radio from '@baserow/modules/core/components/Radio'

export default {
  name: 'ViewOwnershipRadio',
  components: { Radio },
  props: {
    viewOwnershipType: {
      type: Object,
      required: true,
    },
    selectedType: {
      type: String,
      required: true,
    },
  },
  methods: {
    input(value) {
      if (!this.viewOwnershipType.isDeactivated()) {
        this.$emit('input', value)
      } else if (this.viewOwnershipType.getDeactivatedModal()) {
        this.$refs.deactivatedClickModal.show()
      }
    },
  },
}
</script>
