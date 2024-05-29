<template>
  <FormGroup :label="$t('dropdownOptionSelector.label')" small-label>
    <div class="dropdown-option-selector__heading margin-bottom-1">
      <div>
        {{ $t('dropdownOptionSelector.value') }}
      </div>
      <div class="dropdown-option-selector__name-heading">
        {{ $t('dropdownOptionSelector.name') }}
      </div>
    </div>
    <DropdownOption
      v-for="option in options"
      :key="option.id"
      :option="option"
      @update="$emit('update', option, $event)"
      @delete="$emit('delete', option)"
    />
    <ButtonText
      type="secondary"
      size="small"
      icon="iconoir-plus"
      :loading="loading"
      @click="$emit('create')"
    >
      {{ $t('dropdownOptionSelector.addOption') }}
    </ButtonText>
  </FormGroup>
</template>

<script>
import DropdownOption from '@baserow/modules/builder/components/elements/components/forms/general/dropdown/DropdownOption.vue'
export default {
  name: 'DropdownOptionsSelector',
  components: { DropdownOption },
  props: {
    options: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
}
</script>
