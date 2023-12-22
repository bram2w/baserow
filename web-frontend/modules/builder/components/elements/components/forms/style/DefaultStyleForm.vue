<template>
  <form @submit.prevent>
    <StyleBoxForm
      v-for="{ name, label } in borders"
      :key="name"
      v-model="boxStyles[name]"
      :label="label"
      :padding-is-allowed="isStyleAllowed(`style_padding_${name}`)"
      :border-is-allowed="isStyleAllowed(`style_border_${name}`)"
    />
    <FormGroup
      v-if="isStyleAllowed('style_background')"
      :label="$t('defaultStyleForm.backgroundLabel')"
    >
      <Dropdown v-model="values.style_background">
        <DropdownItem
          v-for="type in Object.values(BACKGROUND_TYPES)"
          :key="type.value"
          :name="$t(type.name)"
          :value="type.value"
        />
      </Dropdown>
      <ColorInputGroup
        v-if="
          values.style_background === BACKGROUND_TYPES.COLOR.value &&
          isStyleAllowed('style_background_color')
        "
        v-model="values.style_background_color"
        label-after
        class="margin-top-2"
        :label="$t('defaultStyleForm.backgroundColor')"
        :color-variables="colorVariables"
      />
    </FormGroup>
    <FormGroup
      v-if="isStyleAllowed('style_width')"
      :label="$t('defaultStyleForm.widthLabel')"
    >
      <Dropdown v-model="values.style_width">
        <DropdownItem
          v-for="type in Object.values(WIDTH_TYPES)"
          :key="type.value"
          :name="$t(type.name)"
          :value="type.value"
        ></DropdownItem> </Dropdown
    ></FormGroup>
  </form>
</template>

<script>
import StyleBoxForm from '@baserow/modules/builder/components/elements/components/forms/style/StyleBoxForm'
import styleForm from '@baserow/modules/builder/mixins/styleForm'
import { BACKGROUND_TYPES, WIDTH_TYPES } from '@baserow/modules/builder/enums'

export default {
  components: { StyleBoxForm },
  mixins: [styleForm],
  computed: {
    BACKGROUND_TYPES: () => BACKGROUND_TYPES,
    WIDTH_TYPES: () => WIDTH_TYPES,
  },
}
</script>
