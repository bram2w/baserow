<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action tree__action--has-options" data-sortable-handle>
      <a class="tree__link" @click="$emit('selected', application)">
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
        <div class="context__menu-title">{{ application.name }}</div>
        <ul class="context__menu">
          <slot name="context"></slot>
          <li>
            <a @click="enableRename()">
              <i class="context__menu-icon fas fa-fw fa-pen"></i>
              {{
                $t('sidebarApplication.renameApplication', {
                  type: application._.type.name.toLowerCase(),
                })
              }}
            </a>
          </li>
          <li>
            <a
              :class="{
                'context__menu-item--loading': duplicateLoading,
                disabled: duplicateLoading || deleteLoading,
              }"
              @click="duplicateApplication()"
            >
              <i class="context__menu-icon fas fa-fw fa-copy"></i>
              {{
                $t('sidebarApplication.duplicateApplication', {
                  type: application._.type.name.toLowerCase(),
                })
              }}
            </a>
          </li>
          <li>
            <a @click="openSnapshots">
              <i class="context__menu-icon fas fa-fw fa-history"></i>
              {{ $t('sidebarApplication.snapshots') }}
            </a>
          </li>
          <SnapshotsModal
            ref="snapshotsModal"
            :application="application"
          ></SnapshotsModal>
          <li>
            <a @click="showApplicationTrashModal">
              <i class="context__menu-icon fas fa-fw fa-recycle"></i>
              {{ $t('sidebarApplication.viewTrash') }}
            </a>
          </li>
          <li>
            <a
              :class="{ 'context__menu-item--loading': deleteLoading }"
              @click="deleteApplication()"
            >
              <i class="context__menu-icon fas fa-fw fa-trash"></i>
              {{
                $t('sidebarApplication.deleteApplication', {
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
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ApplicationService from '@baserow/modules/core/services/application'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import SnapshotsModal from '@baserow/modules/core/components/snapshots/SnapshotsModal'

export default {
  name: 'SidebarApplication',
  components: { TrashModal, SnapshotsModal },
  mixins: [jobProgress],
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
      deleteLoading: false,
      duplicateLoading: false,
    }
  },
  computed: {
    ...mapGetters({
      selectedTable: 'table/getSelected',
    }),
  },
  beforeDestroy() {
    this.stopPollIfRunning()
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
    showError(title, message) {
      this.$store.dispatch(
        'notification/error',
        { title, message },
        { root: true }
      )
    },
    // eslint-disable-next-line require-await
    async onJobFailed() {
      this.duplicateLoading = false
      this.$refs.context.hide()
      this.showError(
        this.$t('clientHandler.notCompletedTitle'),
        this.$t('clientHandler.notCompletedDescription')
      )
    },
    // eslint-disable-next-line require-await
    async onJobPollingError(error) {
      this.duplicateLoading = false
      this.$refs.context.hide()
      notifyIf(error, 'application')
    },
    async onJobDone() {
      const newApplicationId = this.job.duplicated_application.id
      let newApplication
      try {
        newApplication = await this.$store.dispatch('application/fetch', {
          applicationId: newApplicationId,
        })
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        this.duplicateLoading = false
        this.$refs.context.hide()
      }

      // find the matching table in the duplicated application if any
      // otherwise just select the first table and show it
      if (newApplication) {
        if (newApplication.tables.length) {
          let selectTable = newApplication.tables[0]
          const originalSelectedTable = this.selectedTable
          if (originalSelectedTable) {
            for (const table of newApplication.tables) {
              if (table.name === originalSelectedTable.name) {
                selectTable = table
                break
              }
            }
          }
          this.$nuxt.$router.push({
            name: 'database-table',
            params: {
              databaseId: newApplication.id,
              tableId: selectTable.id,
            },
          })
        } else {
          this.$emit('selected', newApplication)
        }
      }
    },
    async duplicateApplication() {
      if (this.duplicateLoading || this.deleteLoading) {
        return
      }

      const application = this.application
      this.duplicateLoading = true

      try {
        const { data: job } = await ApplicationService(
          this.$client
        ).asyncDuplicate(application.id)
        this.startJobPoller(job)
      } catch (error) {
        this.duplicateLoading = false
        notifyIf(error, 'application')
      }
    },
    async deleteApplication() {
      if (this.deleteLoading) {
        return
      }

      this.deleteLoading = true

      try {
        await this.$store.dispatch('application/delete', this.application)
        await this.$store.dispatch('notification/restore', {
          trash_item_type: 'application',
          trash_item_id: this.application.id,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }

      this.deleteLoading = false
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
