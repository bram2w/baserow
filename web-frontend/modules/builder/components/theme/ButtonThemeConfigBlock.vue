<template>
  <div>
    <ThemeConfigBlockSection>
      <template #default>
        <FormGroup horizontal :label="$t('buttonThemeConfigBlock.width')">
          <WidthSelector v-model="buttonWidth" />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="button_width"
            />
          </template>
        </FormGroup>
        <FormGroup
          v-if="values.button_width === 'auto'"
          horizontal
          :label="$t('buttonThemeConfigBlock.alignment')"
        >
          <HorizontalAlignmentsSelector v-model="values.button_alignment" />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="button_alignment"
            />
          </template>
        </FormGroup>
        <FormGroup
          v-else
          horizontal
          :label="$t('buttonThemeConfigBlock.textAlignment')"
        >
          <HorizontalAlignmentsSelector
            v-model="values.button_text_alignment"
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="button_text_alignment"
            />
          </template>
        </FormGroup>
      </template>
    </ThemeConfigBlockSection>
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
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/HorizontalAlignmentsSelector'
import WidthSelector from '@baserow/modules/builder/components/WidthSelector'

export default {
  name: 'ButtonThemeConfigBlock',
  components: {
    ThemeConfigBlockSection,
    ResetButton,
    WidthSelector,
    HorizontalAlignmentsSelector,
  },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
      allowedValues: [
        'button_background_color',
        'button_hover_background_color',
        'button_text_alignment',
        'button_alignment',
        'button_width',
      ],
    }
  },
  computed: {
    buttonWidth: {
      get() {
        return this.values.button_width
      },
      set(value) {
        // When we change the button width we want to keep the same alignment,
        // it's less confusing to the user.
        this.values.button_width = value
        if (value === 'auto') {
          this.values.button_alignment = this.values.button_text_alignment
        } else {
          this.values.button_text_alignment = this.values.button_alignment
        }
      },
    },
  },
}
</script>
