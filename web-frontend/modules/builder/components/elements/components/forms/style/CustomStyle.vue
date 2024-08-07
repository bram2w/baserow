<template>
  <div class="custom-style">
    <ButtonText
      class="custom-style__button"
      icon="baserow-icon-settings"
      @click="openPanel()"
    />
    <Context ref="context">
      <div v-auto-overflow-scroll class="custom-style__config-blocks">
        <h2>{{ $t('customStyle.themeOverrides') }}</h2>
        <div
          v-for="(themeConfigBlock, index) in themeConfigBlocks"
          :key="themeConfigBlock.getType()"
          class="custom-style__config-block"
        >
          <h2
            v-if="themeConfigBlocks.length > 1"
            class="custom-style__config-block-title"
          >
            {{ themeConfigBlock.label }}
          </h2>
          <ThemeConfigBlock
            ref="configBlocks"
            :theme="theme"
            :default-values="value?.[styleKey]"
            :preview="false"
            :theme-config-block-type="themeConfigBlock"
            :class="{ 'margin-top-3': index >= 1 }"
            :extra-args="extraArgs"
            @values-changed="onValuesChanged($event)"
          />
        </div>
      </div>
    </Context>
  </div>
</template>

<script>
import ThemeConfigBlock from '@baserow/modules/builder/components/theme/ThemeConfigBlock'

export default {
  name: 'CustomStyle',
  components: { ThemeConfigBlock },
  props: {
    value: {
      type: Object,
      required: false,
      default: () => {},
    },
    theme: { type: Object, required: true },
    configBlockTypes: {
      type: Array,
      required: true,
    },
    styleKey: { type: String, required: true },
    extraArgs: {
      type: Object,
      required: false,
      default: () => null,
    },
  },
  data() {
    return {}
  },
  computed: {
    themeConfigBlocks() {
      return this.configBlockTypes.map((confType) =>
        this.$registry.get('themeConfigBlock', confType)
      )
    },
  },
  methods: {
    openPanel() {
      this.$refs.context.toggle(this.$el, 'bottom', 'left', -100, -425)
    },
    onValuesChanged(newValues) {
      this.$emit('input', {
        ...this.value,
        [this.styleKey]: newValues,
      })
    },
    /**
     * With isFormValid and reset we mimic the form mixin API so the forms are reset
     * when an error happens during the update request.
     */
    isFormValid() {
      return (this.$refs.configBlocks || [])
        .map((confBlock) => confBlock.isFormValid())
        .every((v) => v)
    },
    async reset() {
      await this.$nextTick() // Wait the default value to be updated
      return (this.$refs.configBlocks || []).forEach((confBlock) =>
        confBlock.reset()
      )
    },
  },
}
</script>
