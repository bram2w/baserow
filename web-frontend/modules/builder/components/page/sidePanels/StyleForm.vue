<template>
  <form @submit.prevent>
    <StyleBoxForm v-model="boxStyles.top" :label="$t('styleForm.boxTop')" />
    <StyleBoxForm
      v-model="boxStyles.bottom"
      :label="$t('styleForm.boxBottom')"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import StyleBoxForm from '@baserow/modules/builder/components/page/sidePanels/StyleBoxForm'

export default {
  components: { StyleBoxForm },
  mixins: [form],
  props: {},
  data() {
    return {
      allowedValues: ['style_padding_top', 'style_padding_bottom'],
      values: {
        style_padding_top: 0,
        style_padding_bottom: 0,
      },
      boxStyles: Object.fromEntries(
        ['top', 'bottom'].map((pos) => [pos, this.getBoxStyleValue(pos)])
      ),
    }
  },
  watch: {
    boxStyles: {
      deep: true,
      handler(newValue) {
        Object.entries(newValue).forEach(([prop, value]) => {
          this.setBoxStyleValue(prop, value)
        })
      },
    },
  },
  methods: {
    getBoxStyleValue(pos) {
      return { padding: this.defaultValues[`style_padding_${pos}`] }
    },
    setBoxStyleValue(pos, newValue) {
      if (newValue.padding !== undefined) {
        this.values[`style_padding_${pos}`] = newValue.padding
      }
    },
  },
}
</script>
