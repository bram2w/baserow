<template>
  <div>
    <p class="dashboard-filter-settings__help">
      {{ $t('dashboardFilter.sourceOptionsHelp') }}
    </p>
    <FormGroup
      :label="$t('dashboardFilter.optionValue')"
      small-label
      class="margin-bottom-2"
    >
      <InjectedFormulaInput
        :model-value="filter.formula_value || {}"
        :disabled="disabled"
        @update:model-value="$emit('save', { formula_value: $event })"
      />
    </FormGroup>
  </div>
</template>

<script setup>
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'

defineProps({
  filter: { type: Object, required: true },
  disabled: Boolean,
})
defineEmits(['save'])
</script>
