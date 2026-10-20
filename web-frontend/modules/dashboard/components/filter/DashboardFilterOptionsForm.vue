<template>
  <div>
    <FormGroup
      :label="$t('dashboardFilter.options')"
      small-label
      class="margin-bottom-2"
    >
      <RadioGroup
        :model-value="filter.option_type || 'manual'"
        :options="[
          { label: $t('dashboardFilter.manualOptions'), value: 'manual' },
          { label: $t('dashboardFilter.sourceOptions'), value: 'formulas' },
        ]"
        :disabled="disabled"
        type="button"
        @update:model-value="$emit('save', { option_type: $event })"
      />
    </FormGroup>
    <template v-if="filter.option_type !== 'formulas'">
      <div
        v-for="(option, index) in options"
        :key="index"
        class="dashboard-filter-settings__option"
      >
        <FormGroup :label="$t('dashboardFilter.optionLabel')" small-label>
          <FormInput
            v-model="option.name"
            :maxlength="255"
            :disabled="disabled"
          />
        </FormGroup>
        <FormGroup :label="$t('dashboardFilter.optionValue')" small-label>
          <FormInput
            v-model="option.value"
            :placeholder="option.name"
            :disabled="disabled"
          />
        </FormGroup>
        <ButtonIcon
          icon="iconoir-bin"
          :aria-label="$t('dashboardFilter.removeOption')"
          :disabled="disabled"
          @click="options.splice(index, 1)"
        />
      </div>
      <p v-if="!valid" class="error">
        {{ $t('dashboardFilter.optionsInvalid') }}
      </p>
      <div class="actions actions--gap">
        <ButtonText
          icon="iconoir-plus"
          :disabled="disabled"
          @click="options.push({ name: '', value: '' })"
        >
          {{ $t('dashboardFilter.addOption') }}
        </ButtonText>
        <Button
          type="secondary"
          size="small"
          :disabled="disabled || !valid || !changed"
          @click="$emit('save', { options: resolvedOptions })"
        >
          {{ $t('action.save') }}
        </Button>
      </div>
    </template>
    <template v-else>
      <p class="dashboard-filter-settings__help">
        {{ $t('dashboardFilter.sourceOptionsHelp') }}
      </p>
      <FormGroup
        :label="$t('dashboardFilter.optionLabel')"
        small-label
        class="margin-bottom-2"
      >
        <InjectedFormulaInput
          :model-value="filter.formula_name || {}"
          :disabled="disabled"
          @update:model-value="$emit('save', { formula_name: $event })"
        />
      </FormGroup>
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
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'

const props = defineProps({
  filter: { type: Object, required: true },
  disabled: Boolean,
})
defineEmits(['save'])
const options = ref([])
watch(
  () => [props.filter.id, props.filter.options],
  () => {
    options.value = (props.filter.options || []).map((option) => ({
      ...option,
    }))
  },
  { immediate: true }
)
const resolvedOptions = computed(() =>
  options.value.map(({ name, value }) => ({ name, value: value || name }))
)
const valid = computed(
  () =>
    resolvedOptions.value.every(
      ({ name, value }) => name.trim() && value.trim()
    ) &&
    new Set(resolvedOptions.value.map(({ value }) => value)).size ===
      options.value.length
)
const changed = computed(
  () =>
    JSON.stringify(resolvedOptions.value) !==
    JSON.stringify(props.filter.options || [])
)
</script>
