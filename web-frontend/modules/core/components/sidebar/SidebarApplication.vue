<template>
  <li
    class="tree-item"
    :class="{
      active: application._.selected,
      'tree-item-loading': application._.loading
    }"
  >
    <div class="tree-action">
      <a class="tree-link" @click="selectApplication(application)">
        <i
          class="tree-type fas"
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
        class="tree-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <Context ref="context">
        <div class="context-menu-title">{{ application.name }}</div>
        <ul class="context-menu">
          <li>
            <a @click="enableRename()">
              <i class="context-menu-icon fas fa-fw fa-pen"></i>
              Rename {{ application._.type.name | lowercase }}
            </a>
          </li>
          <li>
            <a @click="deleteApplication(application)">
              <i class="context-menu-icon fas fa-fw fa-trash"></i>
              Delete {{ application._.type.name | lowercase }}
            </a>
          </li>
        </ul>
      </Context>
    </div>
    <template
      v-if="
        application._.selected && application._.type.hasSelectedSidebarComponent
      "
    >
      <component
        :is="getSelectedApplicationComponent(application)"
        :application="application"
      ></component>
    </template>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'SidebarApplication',
  props: {
    application: {
      type: Object,
      required: true
    }
  },
  methods: {
    setLoading(application, value) {
      this.$store.dispatch('application/setItemLoading', {
        application,
        value: value
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
            name: event.value
          }
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
            id: application.id
          }
        },
        () => {
          this.setLoading(application, false)
        },
        () => {
          this.setLoading(application, false)
        }
      )
    },
    async deleteApplication(application) {
      this.$refs.context.hide()
      this.setLoading(application, true)

      try {
        await this.$store.dispatch('application/delete', application)
      } catch (error) {
        notifyIf(error, 'application')
      }

      this.setLoading(application, false)
    },
    getSelectedApplicationComponent(application) {
      const type = this.$store.getters['application/getType'](application.type)
      return type.getSelectedSidebarComponent()
    }
  }
}
</script>
