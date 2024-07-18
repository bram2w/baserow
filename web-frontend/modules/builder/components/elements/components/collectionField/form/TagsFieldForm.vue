<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup
      small-label
      :label="$t('tagsFieldForm.fieldValuesLabel')"
      class="margin-bottom-2"
      horizontal
      required
    >
      <InjectedFormulaInput
        v-model="values.values"
        :placeholder="$t('tagsFieldForm.fieldValuesPlaceholder')"
      />
    </FormGroup>

    <div>
      <FormGroup
        v-if="values.colors_is_formula"
        small-label
        :label="$t('tagsFieldForm.fieldColorsLabel')"
        horizontal
        class="margin-bottom-2"
        required
      >
        <InjectedFormulaInput
          v-model="values.colors"
          :placeholder="$t('tagsFieldForm.fieldColorsPlaceholder')"
        />
        <template #after-input>
          <ButtonIcon
            icon="iconoir-color-picker"
            type="secondary"
            @click="setColorsToPicker"
          />
        </template>
      </FormGroup>
      <FormGroup
        v-else
        horizontal
        small-label
        :label="$t('tagsFieldForm.fieldColorsLabel')"
        class="margin-bottom-2"
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
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'
import collectionFieldForm from '@baserow/modules/builder/mixins/collectionFieldForm'

export default {
  name: 'TagsField',
  components: { InjectedFormulaInput },
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
