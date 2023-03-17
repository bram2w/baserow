<template>
  <div>
    <a
      ref="button"
      class="header__filter-link"
      @click="$refs.context.toggle($refs.button)"
    >
      <i class="header__filter-icon fas fa-stream"></i>
      <span class="header__filter-name">{{
        $t('pageHeaderElements.label')
      }}</span>
    </a>
    <ElementsContext ref="context" />
  </div>
</template>

<script>
import ElementsContext from '@baserow/modules/builder/components/elements/ElementsContext'
export default {
  name: 'PageHeaderElements',
  components: { ElementsContext },
}
</script>
