<template>
  <div class="lang-picker">
    <a
      ref="dropdownLink"
      class="lang-picker__link"
      @click="$refs.dropdown.toggle($refs.dropdownLink)"
    >
      {{ visibleLanguageName }}
      <i class="iconoir-nav-arrow-down lang-picker__icon"></i>
    </a>
    <LanguageSwitcherDropdown
      ref="dropdown"
      class="lang-picker__dropdown"
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
