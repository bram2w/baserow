<template>
  <StyleForm
    :key="element.id"
    ref="panelForm"
    :default-values="element"
    @values-changed="onChange($event)"
  />
</template>

<script>
import elementSidePanel from '@baserow/modules/builder/mixins/elementSidePanel'
import StyleForm from '@baserow/modules/builder/components/page/sidePanels/StyleForm.vue'

export default {
  name: 'StyleSidePanel',
  components: { StyleForm },
  mixins: [elementSidePanel],
}
</script>
