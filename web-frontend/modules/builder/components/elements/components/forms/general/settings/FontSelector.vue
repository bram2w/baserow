<template>
  <FormElement class="control">
    <label class="control__label">
      {{ $t('fontSidePanelForm.label') }}
    </label>
    <div class="control__elements">
      <div class="color-input">
        <ColorPickerContext
          ref="colorPicker"
          v-model="values.font_color"
          :variables="colorVariables"
        ></ColorPickerContext>
        <a
          ref="fontColor"
          class="color-input__preview"
          :style="{
            'background-color': resolveColor(values.font_color, colorVariables),
          }"
          @click="$refs.colorPicker.toggle($refs.fontColor)"
        ></a>
      </div>
    </div>
  </FormElement>
</template>

<script>
import ColorPickerContext from '@baserow/modules/core/components/ColorPickerContext'
import form from '@baserow/modules/core/mixins/form'
import { resolveColor } from '@baserow/modules/core/utils/colors'

export default {
  name: 'FontSelector',
  components: { ColorPickerContext },
  mixins: [form],
  props: {
    colorVariables: {
      type: Array,
      required: true,
    },
  },
  data() {
    return { values: { font_color: 'primary' } }
  },
  methods: { resolveColor },
}
</script>
