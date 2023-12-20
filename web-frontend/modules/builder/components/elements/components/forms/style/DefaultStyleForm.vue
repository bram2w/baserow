<template>
  <form @submit.prevent>
    <StyleBoxForm
      v-model="boxStyles.top"
      :label="$t('defaultStyleForm.boxTop')"
      :padding-is-allowed="isStyleAllowed('style_padding_top')"
      :border-color-is-allowed="isStyleAllowed('style_border_top_color')"
      :border-size-is-allowed="isStyleAllowed('style_border_top_size')"
    />
    <StyleBoxForm
      v-model="boxStyles.bottom"
      :label="$t('defaultStyleForm.boxBottom')"
      :padding-is-allowed="isStyleAllowed('style_padding_bottom')"
      :border-color-is-allowed="isStyleAllowed('style_border_bottom_color')"
      :border-size-is-allowed="isStyleAllowed('style_border_bottom_size')"
    />
    <FormElement v-if="isStyleAllowed('style_background')" class="control">
      <label class="control__label">{{
        $t('defaultStyleForm.backgroundLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown v-model="values.style_background">
          <DropdownItem
            v-for="type in Object.values(BACKGROUND_TYPES)"
            :key="type.value"
            :name="$t(type.name)"
            :value="type.value"
          ></DropdownItem>
        </Dropdown>
        <div
          v-if="
            values.style_background === BACKGROUND_TYPES.COLOR.value &&
            isStyleAllowed('style_background_color')
          "
          class="color-input margin-top-2"
        >
          <ColorPickerContext
            ref="colorPicker"
            v-model="values.style_background_color"
            :variables="colorVariables"
          ></ColorPickerContext>
          <a
            ref="backgroundColor"
            class="color-input__preview margin-right-2"
            :style="{
              'background-color': resolveColor(
                values.style_background_color,
                colorVariables
              ),
            }"
            @click="$refs.colorPicker.toggle($refs.backgroundColor)"
          ></a>
          {{ $t('defaultStyleForm.backgroundColor') }}
        </div>
      </div>
    </FormElement>
    <FormElement v-if="isStyleAllowed('style_width')" class="control">
      <label class="control__label">{{
        $t('defaultStyleForm.widthLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown v-model="values.style_width">
          <DropdownItem
            v-for="type in Object.values(WIDTH_TYPES)"
            :key="type.value"
            :name="$t(type.name)"
            :value="type.value"
          ></DropdownItem>
        </Dropdown>
      </div>
    </FormElement>
  </form>
</template>

<script>
import StyleBoxForm from '@baserow/modules/builder/components/elements/components/forms/style/StyleBoxForm'
import styleForm from '@baserow/modules/builder/mixins/styleForm'
import { BACKGROUND_TYPES, WIDTH_TYPES } from '@baserow/modules/builder/enums'
import ColorPickerContext from '@baserow/modules/core/components/ColorPickerContext'

export default {
  components: { StyleBoxForm, ColorPickerContext },
  mixins: [styleForm],
  computed: {
    BACKGROUND_TYPES: () => BACKGROUND_TYPES,
    WIDTH_TYPES: () => WIDTH_TYPES,
  },
}
</script>
