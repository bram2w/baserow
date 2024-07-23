<!--
Additional 'sync with external calendar' button for share view link.

This button will be rendered differently depending on view.ical_public
-->
<template>
  <ButtonText
    tag="a"
    type="secondary"
    class="button-text--no-underline"
    :icon="iconCssClasses"
    @click="onClick"
  >
    {{
      view.ical_public
        ? $t('calendarViewType.sharedViewDisableSyncToExternalCalendar')
        : $t('calendarViewType.sharedViewEnableSyncToExternalCalendar')
    }}
  </ButtonText>
</template>
<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'CalendarCreateIcalSharedViewLink',
  props: {
    view: { type: Object, required: false, default: null },
  },
  computed: {
    iconCssClasses() {
      const css = this.view.ical_public
        ? ['iconoir-cancel', 'view_sharing__create-link-icon']
        : ['iconoir-calendar']

      return css.join(' ')
    },
  },
  methods: {
    async onClick(evt) {
      await this.updateView({ ical_public: !this.view.ical_public })
      this.$emit('update-view', { ...this.view })
    },

    async updateView(values) {
      const view = this.view

      try {
        await this.$store.dispatch('view/update', {
          view,
          values,
          refreshFromFetch: true,
        })
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
</script>
