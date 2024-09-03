<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ThemeConfigBlockSection>
      <template #default>
        <FormGroup
          horizontal-narrow
          small-label
          required
          class="margin-bottom-2"
          :label="$t('linkThemeConfigBlock.fontFamily')"
        >
          <FontFamilySelector v-model="values.link_font_family" />
          <template #after-input>
            <ResetButton
              v-model="values.link_font_family"
              :default-value="theme?.link_font_family"
            />
          </template>
        </FormGroup>
        <FormGroup
          v-if="!extraArgs?.noAlignment"
          horizontal-narrow
          small-label
          required
          class="margin-bottom-2"
          :label="$t('linkThemeConfigBlock.alignment')"
        >
          <HorizontalAlignmentsSelector v-model="values.link_text_alignment" />
          <template #after-input>
            <ResetButton
              v-model="values.link_text_alignment"
              :default-value="theme?.link_text_alignment"
            />
          </template>
        </FormGroup>
      </template>
    </ThemeConfigBlockSection>
    <ThemeConfigBlockSection :title="$t('linkThemeConfigBlock.defaultState')">
      <template #default>
        <FormGroup
          horizontal-narrow
          small-label
          required
          class="margin-bottom-2"
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
              v-model="values.link_text_color"
              :default-value="theme?.link_text_color"
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
          horizontal-narrow
          small-label
          required
          class="margin-bottom-2"
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
              v-model="values.link_hover_text_color"
              :default-value="theme?.link_hover_text_color"
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
  </form>
</template>

<script>
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'
import ResetButton from '@baserow/modules/builder/components/theme/ResetButton'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/HorizontalAlignmentsSelector'
import FontFamilySelector from '@baserow/modules/builder/components/FontFamilySelector'

export default {
  name: 'LinkThemeConfigBlock',
  components: {
    ThemeConfigBlockSection,
    ResetButton,
    HorizontalAlignmentsSelector,
    FontFamilySelector,
  },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
    }
  },
  methods: {
    isAllowedKey(key) {
      return key.startsWith('link_')
    },
  },
}
</script>
