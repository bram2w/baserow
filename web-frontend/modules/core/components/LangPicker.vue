<template>
  <div v-if="$env.ENABLE_I18N" class="lang-picker">
    <a
      class="lang-picker__link"
      ref="dropdownLink"
      @click="$refs.dropdown.toggle($refs.dropdownLink)"
    >
      {{ visibleLanguageName }}
      <i class="fa fa-caret-down lang-picker__icon"></i>
    </a>
    <LanguageSwitcherDropdown
      class="lang-picker__dropdown"
      ref="dropdown"
      :show-input="false"
    />
  </div>
</template>

<script>
import LanguageSwitcherDropdown from '@baserow/modules/core/components/LangSwitcherDropdown'

export default {
  components: { LanguageSwitcherDropdown },
  computed: {
    visibleLanguageName() {
      for (let i = 0; i < this.$i18n.locales.length; i++) {
        if (this.$i18n.locales[i].code === this.$i18n.locale) {
          return this.$i18n.locales[i].name
        }
      }
      return ''
    },
  },
}
</script>
