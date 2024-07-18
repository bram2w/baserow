<template>
  <ThemeConfigBlockSection>
    <template #default>
      <FormGroup
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.backgroundColor')"
      >
        <ColorInput
          v-model="values.page_background_color"
          small
          :allow-opacity="false"
          :color-variables="colorVariables"
        />
      </FormGroup>
      <FormGroup
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.backgroundImage')"
      >
        <ImageInput v-model="values.page_background_file" />
      </FormGroup>
      <FormGroup
        v-if="values.page_background_file"
        horizontal-narrow
        small-label
        class="margin-bottom-2"
        :label="$t('pageThemeConfigBlock.backgroundMode')"
      >
        <RadioGroup
          v-model="values.page_background_mode"
          type="button"
          :options="backgroundModes"
        />
      </FormGroup>
    </template>
  </ThemeConfigBlockSection>
</template>

<script>
import themeConfigBlock from '@baserow/modules/builder/mixins/themeConfigBlock'
import ThemeConfigBlockSection from '@baserow/modules/builder/components/theme/ThemeConfigBlockSection'
import { BACKGROUND_MODES } from '@baserow/modules/builder/enums'

export default {
  name: 'PageThemeConfigBlock',
  components: { ThemeConfigBlockSection },
  mixins: [themeConfigBlock],
  data() {
    return {
      values: {},
    }
  },
  computed: {
    backgroundModes() {
      return [
        {
          label: this.$t('backgroundModes.tile'),
          value: BACKGROUND_MODES.TILE,
        },
        {
          label: this.$t('backgroundModes.fill'),
          value: BACKGROUND_MODES.FILL,
        },
        {
          label: this.$t('backgroundModes.fit'),
          value: BACKGROUND_MODES.FIT,
        },
      ]
    },
  },
  methods: {
    isAllowedKey(key) {
      return key.startsWith('page_')
    },
  },
}
</script>
