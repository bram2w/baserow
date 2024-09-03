<template>
  <component
    :is="elementType.generalFormComponent"
    :key="element.id"
    ref="panelForm"
    class="element-form"
    :default-values="defaultValues"
    @values-changed="onChange($event)"
  />
</template>

<script>
import elementSidePanel from '@baserow/modules/builder/mixins/elementSidePanel'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'GeneralSidePanel',
  mixins: [elementSidePanel],
  inject: ['applicationContext'],
  provide() {
    return {
      applicationContext: {
        ...this.applicationContext,
        element: this.element,
      },
      dataProvidersAllowed: DATA_PROVIDERS_ALLOWED_ELEMENTS,
    }
  },
}
</script>
