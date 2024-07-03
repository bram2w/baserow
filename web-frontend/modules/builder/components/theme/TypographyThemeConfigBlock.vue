<template>
  <div>
    <ThemeConfigBlockSection
      v-for="i in headings"
      :key="i"
      :title="$t('typographyThemeConfigBlock.headingLabel', { i })"
    >
      <template #default>
        <FormGroup horizontal :label="$t('typographyThemeConfigBlock.size')">
          <div
            class="input__with-icon heading-theme-config-block__input-number"
          >
            <input
              v-model="values[`heading_${i}_font_size`]"
              type="number"
              class="input remove-number-input-controls input--small"
              :min="fontSizeMin"
              :max="fontSizeMax"
              :class="{
                'input--error': $v.values[`heading_${i}_font_size`].$invalid,
              }"
              @blur="$v.values[`heading_${i}_font_size`].$touch()"
            />
            <i>px</i>
          </div>
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`heading_${i}_font_size`"
            />
          </template>
        </FormGroup>
        <FormGroup horizontal :label="$t('typographyThemeConfigBlock.color')">
          <ColorInput
            v-model="values[`heading_${i}_text_color`]"
            :color-variables="colorVariables"
            :default-value="theme ? theme[`heading_${i}_text_color`] : null"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`heading_${i}_text_color`"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <component
          :is="`h${i}`"
          class="margin-bottom-2 theme-settings__section-ellipsis"
          :class="`ab-heading--h${i}`"
        >
          {{ $t('typographyThemeConfigBlock.headingValue', { i }) }}
        </component>
      </template>
    </ThemeConfigBlockSection>
  </div>
</template>

<script>
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'
import ResetButton from '@baserow/modules/builder/components/theme/ResetButton'

const fontSizeMin = 1
const fontSizeMax = 100
const headings = [1, 2, 3]

export default {
  name: 'TypographyThemeConfigBlock',
  components: { ThemeConfigBlockSection, ResetButton },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
      allowedValues: headings
        .map((level) => [
          `heading_${level}_text_color`,
          `heading_${level}_font_size`,
        ])
        .flat(),
    }
  },
  computed: {
    headings() {
      if (this.element?.level) {
        return [this.element.level]
      } else {
        return headings
      }
    },
    fontSizeMin() {
      return fontSizeMin
    },
    fontSizeMax() {
      return fontSizeMax
    },
  },
  validations: {
    values: headings.reduce((o, i) => {
      o[`heading_${i}_font_size`] = {
        required,
        integer,
        minValue: minValue(fontSizeMin),
        maxValue: maxValue(fontSizeMax),
      }
      return o
    }, {}),
  },
}
</script>
