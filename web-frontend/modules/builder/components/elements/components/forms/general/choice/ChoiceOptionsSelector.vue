<template>
  <FormGroup :label="$t('choiceOptionSelector.label')" small-label>
    <div class="dropdown-option-selector__heading margin-bottom-1">
      <div>
        {{ $t('choiceOptionSelector.value') }}
      </div>
      <div class="dropdown-option-selector__name-heading">
        {{ $t('choiceOptionSelector.name') }}
      </div>
    </div>
    <ChoiceOption
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
      {{ $t('choiceOptionSelector.addOption') }}
    </ButtonText>
  </FormGroup>
</template>

<script>
import ChoiceOption from '@baserow/modules/builder/components/elements/components/forms/general/choice/ChoiceOption.vue'
export default {
  name: 'ChoiceOptionsSelector',
  components: { ChoiceOption },
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
