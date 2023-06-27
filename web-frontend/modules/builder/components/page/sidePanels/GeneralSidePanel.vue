<template>
  <component
    :is="elementType.formComponent"
    :key="element.id"
    ref="elementForm"
    class="element-form"
    :builder="builder"
    :default-values="defaultValues"
    @values-changed="onChange($event)"
  />
</template>

<script>
import elementSidePanel from '@baserow/modules/builder/mixins/elementSidePanel'

export default {
  name: 'GeneralSidePanel',
  mixins: [elementSidePanel],
}
</script>
