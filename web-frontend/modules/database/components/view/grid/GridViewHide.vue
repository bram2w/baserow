<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        'active--primary': hiddenFields.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-eye-slash"></i>
      <span v-if="hiddenFields.length === 1"
        >{{ hiddenFields.length }} hidden field</span
      >
      <span v-else-if="hiddenFields.length > 1"
        >{{ hiddenFields.length }} hidden fields</span
      >
      <span v-else>Hide fields</span>
    </a>
    <GridViewHideContext
      ref="context"
      :view="view"
      :fields="fields"
    ></GridViewHideContext>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import GridViewHideContext from '@baserow/modules/database/components/view/grid/GridViewHideContext'

export default {
  name: 'GridViewHide',
  components: { GridViewHideContext },
  props: {
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    hiddenFields() {
      return this.fields.filter((field) => {
        const exists = Object.prototype.hasOwnProperty.call(
          this.fieldOptions,
          field.id
        )
        return !exists || (exists && this.fieldOptions[field.id].hidden)
      })
    },
    ...mapGetters({
      fieldOptions: 'view/grid/getAllFieldOptions',
    }),
  },
}
</script>
