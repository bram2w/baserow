<template>
  <nuxt-link
    class="notification-panel__notification-link"
    event=""
    :to="url"
    @click.native="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n path="rowCommentMentionNotification.title" tag="span">
        <template #sender>
          <strong>{{ notification.sender.first_name }}</strong>
        </template>
        <template #table>
          <strong>{{ notification.data.table_name }}</strong>
        </template>
      </i18n>
    </div>
    <RichTextEditor :editable="false" :value="notification.data.message" />
  </nuxt-link>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'
import notificationContent from '@baserow/modules/core/mixins/notificationContent'
import { openRowEditModal } from '@baserow/modules/database/utils/router'

export default {
  name: 'RowCommentMentionNotification',
  components: {
    RichTextEditor,
  },
  mixins: [notificationContent],
  props: {
    notification: {
      type: Object,
      required: true,
    },
  },
  computed: {
    params() {
      const data = this.notification.data
      return {
        databaseId: data.database_id,
        tableId: data.table_id,
        rowId: data.row_id,
      }
    },
    url() {
      return {
        name: 'database-table-row',
        params: this.params,
      }
    },
  },
  methods: {
    async handleClick(evt) {
      evt.preventDefault()
      this.$emit('close-panel')
      const { $store, $router, $route } = this
      await openRowEditModal({ $store, $router, $route }, this.params)
    },
  },
}
</script>
