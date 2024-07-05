<template>
  <div>
    <ThemeConfigBlockSection>
      <template #default>
        <FormGroup
          horizontal
          small-label
          required
          :label="$t('linkThemeConfigBlock.alignment')"
          class="margin-bottom-1"
        >
          <HorizontalAlignmentsSelector v-model="values.link_text_alignment" />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="link_text_alignment"
            />
          </template>
        </FormGroup>
      </template>
    </ThemeConfigBlockSection>
    <ThemeConfigBlockSection :title="$t('linkThemeConfigBlock.defaultState')">
      <template #default>
        <FormGroup
          horizontal
          small-label
          required
          class="margin-bottom-1"
          :label="$t('linkThemeConfigBlock.color')"
        >
          <ColorInput
            v-model="values.link_text_color"
            :color-variables="colorVariables"
            :default-value="theme?.link_text_color"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="link_text_color"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <ABLink url="">{{ $t('linkThemeConfigBlock.link') }}</ABLink>
      </template>
    </ThemeConfigBlockSection>
    <ThemeConfigBlockSection :title="$t('linkThemeConfigBlock.hoverState')">
      <template #default>
        <FormGroup
          horizontal
          small-label
          required
          class="margin-bottom-1"
          :label="$t('linkThemeConfigBlock.color')"
        >
          <ColorInput
            v-model="values.link_hover_text_color"
            :color-variables="colorVariables"
            :default-value="theme?.link_hover_text_color"
            small
          />
          <template #after-input>
            <ResetButton
              v-model="values"
              :theme="theme"
              property="link_hover_text_color"
            />
          </template>
        </FormGroup>
      </template>
      <template #preview>
        <ABLink url="" class="ab-link--force-hover">
          {{ $t('linkThemeConfigBlock.link') }}
        </ABLink>
      </template>
    </ThemeConfigBlockSection>
  </div>
</template>

<script>
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'
import ResetButton from '@baserow/modules/builder/components/theme/ResetButton'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/HorizontalAlignmentsSelector'

export default {
  name: 'LinkThemeConfigBlock',
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
        'link_text_color',
        'link_hover_text_color',
        'link_text_alignment',
      ],
    }
  },
}
</script>
