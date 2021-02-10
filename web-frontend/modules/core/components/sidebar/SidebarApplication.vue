<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action tree__action--has-options">
      <a class="tree__link" @click="selectApplication(application)">
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
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <Context ref="context">
        <div class="context__menu-title">{{ application.name }}</div>
        <ul class="context__menu">
          <component
            :is="contextComponent"
            :application="application"
          ></component>
          <li>
            <a @click="enableRename()">
              <i class="context__menu-icon fas fa-fw fa-pen"></i>
              Rename {{ application._.type.name | lowercase }}
            </a>
          </li>
          <li>
            <a @click="deleteApplication()">
              <i class="context__menu-icon fas fa-fw fa-trash"></i>
              Delete {{ application._.type.name | lowercase }}
            </a>
          </li>
        </ul>
        <DeleteApplicationModal
          ref="deleteApplicationModal"
          :application="application"
        />
      </Context>
    </div>
    <template
      v-if="
        application._.selected && application._.type.hasSelectedSidebarComponent
      "
    >
      <component
        :is="selectedApplicationComponent"
        :application="application"
      ></component>
    </template>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import DeleteApplicationModal from './DeleteApplicationModal'

export default {
  name: 'SidebarApplication',
  components: { DeleteApplicationModal },
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  computed: {
    selectedApplicationComponent() {
      return this.$registry
        .get('application', this.application.type)
        .getSelectedSidebarComponent()
    },
    contextComponent() {
      return this.$registry
        .get('application', this.application.type)
        .getContextComponent()
    },
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
    async selectApplication(application) {
      // If there is no route associated with the application we just change the
      // selected state.
      if (application._.type.routeName === null) {
        try {
          await this.$store.dispatch('application/select', application)
        } catch (error) {
          notifyIf(error, 'group')
        }
        return
      }

      // If we do have a route, this the related component with that route has to do
      // the state change.
      this.setLoading(application, true)

      this.$nuxt.$router.push(
        {
          name: application._.type.routeName,
          params: {
            id: application.id,
          },
        },
        () => {
          this.setLoading(application, false)
        },
        () => {
          this.setLoading(application, false)
        }
      )
    },
    deleteApplication() {
      this.$refs.context.hide()
      this.$refs.deleteApplicationModal.show()
    },
  },
}
</script>
