<template>
  <Dropdown
    :value="value"
    fixed-items
    class="integration-dropdown"
    :size="size"
    :disabled="disabled || !integrationType"
    :placeholder="
      !integrationType
        ? $t('integrationDropdown.selectTypeFirst')
        : $t('integrationDropdown.integrationPlaceholder')
    "
    show-footer
    @input="$emit('input', $event)"
  >
    <DropdownItem
      v-for="integrationItem in integrations"
      :key="integrationItem.id"
      :name="integrationItem.name"
      :value="integrationItem.id"
    />
    <template #emptyState>
      {{ $t('integrationDropdown.noIntegrations') }}
    </template>
    <template #footer>
      <a
        class="select__footer-button"
        @click="$refs.IntegrationCreateEditModal.show()"
      >
        <i class="iconoir-plus"></i>
        {{ $t('integrationDropdown.addIntegration') }}
      </a>
      <IntegrationCreateEditModal
        v-if="integrationType"
        ref="IntegrationCreateEditModal"
        :application="application"
        :integration-type="integrationType"
        create
        @created="$emit('input', $event.id)"
      />
    </template>
  </Dropdown>
</template>

<script>
import IntegrationCreateEditModal from '@baserow/modules/core/components/integrations/IntegrationCreateEditModal'

export default {
  name: 'IntegrationDropdown',
  components: { IntegrationCreateEditModal },
  props: {
    value: {
      type: Number,
      required: false,
      default: null,
    },
    application: {
      type: Object,
      required: true,
    },
    integrationType: {
      type: Object,
      required: false,
      default: null,
    },
    integrations: {
      type: Array,
      required: true,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    size: {
      type: String,
      required: false,
      default: 'regular',
    },
  },
}
</script>
