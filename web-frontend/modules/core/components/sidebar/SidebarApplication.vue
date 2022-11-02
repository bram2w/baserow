<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action tree__action--has-options" data-sortable-handle>
      <a
        class="tree__link"
        :title="application.name"
        @click="$emit('selected', application)"
      >
        <i
          class="tree__icon tree__icon--type fas"
          :class="'fa-' + application._.type.iconClass"
        ></i>
        <Editable
          ref="rename"
          :value="application.name"
          @change="renameApplication(application, $event)"
        ></Editable>
      </a>
      <a
        ref="contextLink"
        class="tree__options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        @mousedown.stop
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <Context ref="context">
        <div class="context__menu-title">
          {{ application.name }} ({{ application.id }})
        </div>
        <ul class="context__menu">
          <slot name="context"></slot>
          <li
            v-if="
              $hasPermission(
                'application.update',
                application,
                application.group.id
              )
            "
          >
            <a @click="enableRename()">
              <i class="context__menu-icon fas fa-fw fa-pen"></i>
              {{
                $t('sidebarApplication.rename', {
                  type: application._.type.name.toLowerCase(),
                })
              }}
            </a>
          </li>
          <li
            v-if="
              $hasPermission(
                'application.duplicate',
                application,
                application.group.id
              )
            "
          >
            <SidebarDuplicateApplicationContextItem
              :application="application"
              :disabled="deleting"
              @click="$refs.context.hide()"
            ></SidebarDuplicateApplicationContextItem>
          </li>
          <li
            v-if="
              $hasPermission(
                'application.create_snapshot',
                application,
                application.group.id
              )
            "
          >
            <a @click="openSnapshots">
              <i class="context__menu-icon fas fa-fw fa-history"></i>
              {{ $t('sidebarApplication.snapshots') }}
            </a>
          </li>
          <SnapshotsModal
            ref="snapshotsModal"
            :application="application"
          ></SnapshotsModal>
          <li
            v-if="
              $hasPermission(
                'application.read_trash',
                application,
                application.group.id
              )
            "
          >
            <a @click="showApplicationTrashModal">
              <i class="context__menu-icon fas fa-fw fa-recycle"></i>
              {{ $t('sidebarApplication.viewTrash') }}
            </a>
          </li>
          <li
            v-if="
              $hasPermission(
                'application.delete',
                application,
                application.group.id
              )
            "
          >
            <a
              :class="{ 'context__menu-item--loading': deleting }"
              @click="deleteApplication()"
            >
              <i class="context__menu-icon fas fa-fw fa-trash"></i>
              {{
                $t('sidebarApplication.delete', {
                  type: application._.type.name.toLowerCase(),
                })
              }}
            </a>
          </li>
        </ul>
      </Context>
      <TrashModal
        ref="applicationTrashModal"
        :initial-group="group"
        :initial-application="application"
      >
      </TrashModal>
    </div>
    <slot name="body"></slot>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import SidebarDuplicateApplicationContextItem from '@baserow/modules/core/components/sidebar/SidebarDuplicateApplicationContextItem.vue'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import SnapshotsModal from '@baserow/modules/core/components/snapshots/SnapshotsModal'

export default {
  name: 'SidebarApplication',
  components: {
    TrashModal,
    SidebarDuplicateApplicationContextItem,
    SnapshotsModal,
  },
  props: {
    application: {
      type: Object,
      required: true,
    },
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      deleting: false,
    }
  },
  methods: {
    setLoading(application, value) {
      this.$store.dispatch('application/setItemLoading', {
        application,
        value,
      })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameApplication(application, event) {
      this.setLoading(application, true)

      try {
        await this.$store.dispatch('application/update', {
          application,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'application')
      }

      this.setLoading(application, false)
    },
    async deleteApplication() {
      if (this.deleting) {
        return
      }

      this.deleting = true

      try {
        await this.$store.dispatch('application/delete', this.application)
        await this.$store.dispatch('notification/restore', {
          trash_item_type: 'application',
          trash_item_id: this.application.id,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }

      this.deleting = false
    },
    showApplicationTrashModal() {
      this.$refs.context.hide()
      this.$refs.applicationTrashModal.show()
    },
    openSnapshots() {
      this.$refs.context.hide()
      this.$refs.snapshotsModal.show()
    },
  },
}
</script>
