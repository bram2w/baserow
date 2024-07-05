<template>
  <div>
    <ThemeConfigBlockSection
      v-if="showBody"
      :title="$t('typographyThemeConfigBlock.bodyLabel')"
      class="margin-bottom-2"
    >
      <template #default>
        <FormGroup
          horizontal
          small-label
          :label="$t('typographyThemeConfigBlock.textAlignment')"
        >
          <HorizontalAlignmentsSelector
            v-model="values[`body_text_alignment`]"
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`body_text_alignment`"
            />
          </template>
        </FormGroup>
        <FormGroup
          horizontal
          small-label
          :label="$t('typographyThemeConfigBlock.size')"
          :error="$v.values[`body_font_size`].$invalid"
        >
          <FormInput
            v-model="values[`body_font_size`]"
            type="number"
            remove-number-input-controls
            :min="fontSizeMin"
            :max="fontSizeMax"
            :error="$v.values[`body_font_size`].$invalid"
            @blur="$v.values[`body_font_size`].$touch()"
          >
            <template #suffix>px</template>
          </FormInput>

          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`body_font_size`"
            />
          </template>
        </FormGroup>
        <FormGroup
          horizontal
          small-label
          :label="$t('typographyThemeConfigBlock.color')"
        >
          <ColorInput
            v-model="values['body_text_color']"
            :color-variables="colorVariables"
            :default-value="theme ? theme['body_text_color'] : null"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="'body_text_color'"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <ABParagraph>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua.
        </ABParagraph>
      </template>
    </ThemeConfigBlockSection>
    <ThemeConfigBlockSection
      v-for="level in headings"
      :key="level"
      :title="$t('typographyThemeConfigBlock.headingLabel', { i: level })"
      class="margin-bottom-2"
    >
      <template #default>
        <FormGroup
          horizontal
          small-label
          :label="$t('typographyThemeConfigBlock.textAlignment')"
        >
          <HorizontalAlignmentsSelector
            v-model="values[`heading_${level}_text_alignment`]"
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`heading_${level}_text_alignment`"
            />
          </template>
        </FormGroup>

        <FormGroup
          horizontal
          small-label
          :label="$t('typographyThemeConfigBlock.size')"
          :error="$v.values[`heading_${level}_font_size`].$invalid"
        >
          <FormInput
            v-model="values[`heading_${level}_font_size`]"
            type="number"
            remove-number-input-controls
            :min="fontSizeMin"
            :max="fontSizeMax"
            :error="$v.values[`heading_${level}_font_size`].$invalid"
            @blur="$v.values[`heading_${level}_font_size`].$touch()"
          >
            <template #suffix>px</template>
          </FormInput>

          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`body_font_size`"
            />
          </template>
        </FormGroup>

        <FormGroup
          horizontal
          small-label
          :label="$t('typographyThemeConfigBlock.color')"
        >
          <ColorInput
            v-model="values[`heading_${level}_text_color`]"
            :color-variables="colorVariables"
            :default-value="theme ? theme[`heading_${level}_text_color`] : null"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              :property="`heading_${level}_text_color`"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <component
          :is="`h${level}`"
          class="margin-bottom-2 theme-settings__section-ellipsis"
          :class="`ab-heading--h${level}`"
        >
          {{ $t('typographyThemeConfigBlock.headingValue', { i: level }) }}
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
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/HorizontalAlignmentsSelector'

const fontSizeMin = 1
const fontSizeMax = 100
const headings = [1, 2, 3, 4, 5, 6]

export default {
  name: 'TypographyThemeConfigBlock',
  components: {
    ThemeConfigBlockSection,
    ResetButton,
    HorizontalAlignmentsSelector,
  },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
      allowedValues: [
        ...headings
          .map((level) => [
            `heading_${level}_text_color`,
            `heading_${level}_font_size`,
            `heading_${level}_text_alignment`,
          ])
          .flat(),
        'body_font_size',
        'body_text_alignment',
        'body_text_color',
      ],
    }
  },
  computed: {
    headings() {
      if (this.extraArgs?.headingLevel) {
        return [this.extraArgs.headingLevel]
      } else {
        return headings
      }
    },
    showBody() {
      return !this.extraArgs?.headingLevel
    },
    fontSizeMin() {
      return fontSizeMin
    },
    fontSizeMax() {
      return fontSizeMax
    },
  },
  validations: {
    values: {
      ...headings.reduce((o, i) => {
        o[`heading_${i}_font_size`] = {
          required,
          integer,
          minValue: minValue(fontSizeMin),
          maxValue: maxValue(fontSizeMax),
        }
        return o
      }, {}),
      body_font_size: {
        required,
        integer,
        minValue: minValue(fontSizeMin),
        maxValue: maxValue(fontSizeMax),
      },
    },
  },
}
</script>
