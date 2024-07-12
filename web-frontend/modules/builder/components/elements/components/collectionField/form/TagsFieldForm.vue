<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.values"
      :label="$t('tagsFieldForm.fieldValuesLabel')"
      :placeholder="$t('tagsFieldForm.fieldValuesPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      horizontal
    />
    <div>
      <ApplicationBuilderFormulaInputGroup
        v-if="values.colors_is_formula"
        v-model="values.colors"
        :label="$t('tagsFieldForm.fieldColorsLabel')"
        :placeholder="$t('tagsFieldForm.fieldColorsPlaceholder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
        horizontal
      >
        <template #after-input>
          <ButtonIcon
            icon="iconoir-color-picker"
            type="secondary"
            @click="setColorsToPicker"
          />
        </template>
      </ApplicationBuilderFormulaInputGroup>
      <FormGroup
        v-else
        horizontal
        small-label
        :label="$t('tagsFieldForm.fieldColorsLabel')"
      >
        <ColorInput
          v-model="values.colors"
          :color-variables="colorVariables"
          small
        />
        <template #after-input>
          <ButtonIcon
            icon="iconoir-sigma-function"
            type="secondary"
            @click="setColorsToFormula"
          />
        </template>
      </FormGroup>
    </div>
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import collectionFieldForm from '@baserow/modules/builder/mixins/collectionFieldForm'

export default {
  name: 'TagsField',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [collectionFieldForm],
  data() {
    return {
      allowedValues: ['values', 'colors', 'colors_is_formula'],
      values: {
        values: '',
        colors: '#acc8f8',
        colors_is_formula: false,
      },
    }
  },
  methods: {
    setColorsToFormula() {
      this.values.colors_is_formula = true
      this.values.colors = `'${this.values.colors}'`
    },
    setColorsToPicker() {
      this.values.colors_is_formula = false
      this.values.colors = '#acc8f8'
    },
  },
}
</script>
