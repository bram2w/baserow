<template>
  <ThemeConfigBlockSection>
    <template #default>
      <FormGroup horizontal :label="$t('colorThemeConfigBlock.primaryColor')">
        <ColorInput v-model="values.primary_color" small />
      </FormGroup>
      <FormGroup horizontal :label="$t('colorThemeConfigBlock.secondaryColor')">
        <ColorInput v-model="values.secondary_color" small />
      </FormGroup>
      <FormGroup horizontal :label="$t('colorThemeConfigBlock.borderColor')">
        <ColorInput v-model="values.border_color" small />
      </FormGroup>
    </template>
  </ThemeConfigBlockSection>
</template>

<script>
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'

export default {
  name: 'ColorThemeConfigBlock',

  components: { ThemeConfigBlockSection },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
      allowedValues: ['primary_color', 'secondary_color', 'border_color'],
    }
  },
}
</script>
