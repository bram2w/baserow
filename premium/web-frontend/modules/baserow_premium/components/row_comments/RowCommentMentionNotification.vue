<template>
  <nuxt-link
    class="notification-panel__notification-link"
    :to="url"
    @click.native="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n path="rowCommentMentionNotification.title" tag="span">
        <template #sender>
          <strong v-if="sender">{{ sender }}</strong>
          <strong v-else
            ><s>{{
              $t('rowCommentMentionNotification.deletedUser')
            }}</s></strong
          >
        </template>
        <template #row>
          <strong>{{
            notification.data.row_name ?? notification.data.row_id
          }}</strong>
        </template>
        <template #table>
          <strong>{{ notification.data.table_name }}</strong>
        </template>
      </i18n>
    </div>
    <RichTextEditor
      :editable="false"
      :enable-mentions="true"
      :value="notification.data.message"
    />
  </nuxt-link>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'
import notificationContent from '@baserow/modules/core/mixins/notificationContent'

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
    handleClick(evt) {
      this.$emit('close-panel')
    },
  },
}
</script>
