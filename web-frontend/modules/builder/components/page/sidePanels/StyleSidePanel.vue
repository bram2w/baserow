<template>
  <div :key="element.id">
    <StyleBoxForm
      :label="$t('styleSidePanel.paddingTop')"
      padding-name="style_padding_top"
      :default-values="defaultValues"
      @values-changed="onChange($event)"
    ></StyleBoxForm>
    <StyleBoxForm
      :label="$t('styleSidePanel.paddingBottom')"
      padding-name="style_padding_bottom"
      :default-values="defaultValues"
      @values-changed="onChange($event)"
    ></StyleBoxForm>
  </div>
</template>

<script>
import elementSidePanel from '@baserow/modules/builder/mixins/elementSidePanel'
import StyleBoxForm from '@baserow/modules/builder/components/page/sidePanels/StyleBoxForm.vue'

export default {
  name: 'StyleSidePanel',
  components: { StyleBoxForm },
  mixins: [elementSidePanel],
}
</script>
