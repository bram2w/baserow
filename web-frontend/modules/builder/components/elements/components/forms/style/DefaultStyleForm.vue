<template>
  <form @submit.prevent>
    <StyleBoxForm
      v-if="isStyleAllowed('style_padding_top')"
      v-model="boxStyles.top"
      :label="$t('defaultStyleForm.boxTop')"
    />
    <StyleBoxForm
      v-if="isStyleAllowed('style_padding_top')"
      v-model="boxStyles.bottom"
      :label="$t('defaultStyleForm.boxBottom')"
    />
  </form>
</template>

<script>
import StyleBoxForm from '@baserow/modules/builder/components/page/sidePanels/StyleBoxForm'
import styleForm from '@baserow/modules/builder/mixins/styleForm'

export default {
  components: { StyleBoxForm },
  mixins: [styleForm],
}
</script>
