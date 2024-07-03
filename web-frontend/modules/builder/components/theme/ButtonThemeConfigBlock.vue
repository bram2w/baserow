<template>
  <div>
    <ThemeConfigBlockSection :title="$t('buttonThemeConfigBlock.defaultState')">
      <template #default>
        <FormGroup
          horizontal
          :label="$t('buttonThemeConfigBlock.backgroundColor')"
        >
          <ColorInput
            v-model="values.button_background_color"
            :color-variables="colorVariables"
            :default-value="theme?.button_background_color"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="button_background_color"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <ABButton>{{ $t('buttonThemeConfigBlock.button') }}</ABButton>
      </template>
    </ThemeConfigBlockSection>
    <ThemeConfigBlockSection :title="$t('buttonThemeConfigBlock.hoverState')">
      <template #default>
        <FormGroup
          horizontal
          :label="$t('buttonThemeConfigBlock.backgroundColor')"
        >
          <ColorInput
            v-model="values.button_hover_background_color"
            :color-variables="colorVariables"
            :default-value="theme?.button_hover_background_color"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="button_hover_background_color"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <ABButton class="ab-button--force-hover">
          {{ $t('buttonThemeConfigBlock.button') }}
        </ABButton>
      </template>
    </ThemeConfigBlockSection>
  </div>
</template>

<script>
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'
import ResetButton from '@baserow/modules/builder/components/theme/ResetButton'

export default {
  name: 'ButtonThemeConfigBlock',
  components: { ThemeConfigBlockSection, ResetButton },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
      allowedValues: [
        'button_background_color',
        'button_hover_background_color',
      ],
    }
  },
}
</script>
