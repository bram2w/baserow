<template>
  <div class="api-token">
    <div class="api-token__head">
      <div class="api-token__info">
        <div class="api-token__name">
          <div class="api-token__name-content">
            <Editable
              ref="rename"
              :value="token.name"
              @change="
                updateToken(
                  token,
                  { name: $event.value },
                  { name: $event.oldValue }
                )
              "
            ></Editable>
          </div>
          <a
            ref="contextLink"
            class="api-token__more"
            @click.prevent="
              $refs.context.toggle($refs.contextLink, 'bottom', 'right', 4)
            "
          >
            <i class="fas fa-ellipsis-h"></i>
          </a>
          <Context ref="context">
            <div class="api-token__key">
              <div class="api-token__key-name">
                {{ $t('apiToken.tokenPrefix') }}
              </div>
              <div class="api-token__key-value">
                <template v-if="tokenVisible">
                  {{ token.key }}
                </template>
                <template v-else>••••••••••••••••••••••••••••••••</template>
              </div>
              <a
                class="api-token__key-visible"
                :title="$t('apiToken.showOrHide')"
                @click.prevent="tokenVisible = !tokenVisible"
              >
                <i
                  class="fas"
                  :class="tokenVisible ? 'fa-eye-slash' : 'fa-eye'"
                ></i>
              </a>
              <a
                class="api-token__key-copy"
                :title="$t('apiToken.copyToClipboard')"
                @click=";[copyTokenToClipboard(), $refs.copied.show()]"
              >
                <i class="fas fa-copy"></i>
                <Copied ref="copied"></Copied>
              </a>
            </div>
            <ul class="context__menu">
              <li>
                <nuxt-link :to="{ name: 'database-api-docs' }">
                  <i class="context__menu-icon fas fa-fw fa-book"></i>
                  {{ $t('apiToken.viewAPIDocs') }}
                </nuxt-link>
              </li>
              <li>
                <a
                  :class="{
                    'context__menu-item--loading': rotateLoading,
                  }"
                  @click="rotateKey(token)"
                >
                  <i class="context__menu-icon fas fa-fw fa-recycle"></i>
                  {{ $t('apiToken.generateNewToken') }}
                </a>
              </li>
              <li>
                <a @click="enableRename()">
                  <i class="context__menu-icon fas fa-fw fa-pen"></i>
                  {{ $t('action.rename') }}
                </a>
              </li>
              <li>
                <a
                  :class="{
                    'context__menu-item--loading': deleteLoading,
                  }"
                  @click.prevent="deleteToken(token)"
                >
                  <i class="context__menu-icon fas fa-fw fa-trash"></i>
                  {{ $t('action.delete') }}
                </a>
              </li>
            </ul>
          </Context>
        </div>
        <div class="api-token__details">
          <div class="api-token__group">{{ group.name }}</div>
          <a class="api-token__expand" @click.prevent="open = !open">
            {{ $t('apiToken.showDatabases') }}
            <i
              class="fas"
              :class="{
                'fa-angle-down': !open,
                'fa-angle-up': open,
              }"
            ></i>
          </a>
        </div>
      </div>
      <div class="api-token__permissions">
        <div
          v-for="(operationName, operation) in operations"
          :key="operation"
          class="api-token__permission"
        >
          {{ operationName }}
          <SwitchInput
            :value="isActive(operation)"
            :large="true"
            @input="toggle(operation, $event)"
          ></SwitchInput>
        </div>
      </div>
    </div>
    <div class="api-token__body" :class="{ 'api-token__body--open': open }">
      <div v-for="database in databases" :key="database.id">
        <div class="api-token__row">
          <div class="api-token__database">
            {{ database.name }} {{ database.id }}
          </div>
          <div class="api-token__permissions">
            <div
              v-for="(operationName, operation) in operations"
              :key="operation"
              class="api-token__permission"
            >
              <SwitchInput
                :value="isDatabaseActive(database, operation)"
                :large="true"
                @input="toggleDatabase(database, databases, operation, $event)"
              ></SwitchInput>
            </div>
          </div>
        </div>
        <div
          v-for="table in database.tables"
          :key="table.id"
          class="api-token__row"
        >
          <div class="api-token__table">
            {{ table.name }} <small>(id: {{ table.id }})</small>
          </div>
          <div class="api-token__permissions">
            <div
              v-for="(operationName, operation) in operations"
              :key="operation"
              class="api-token__permission"
            >
              <Checkbox
                :value="isTableActive(table, database, operation)"
                @input="
                  toggleTable(table, database, databases, operation, $event)
                "
              ></Checkbox>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'
import TokenService from '@baserow/modules/database/services/token'

export default {
  name: 'APIToken',
  props: {
    token: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      open: false,
      deleteLoading: false,
      rotateLoading: false,
      tokenVisible: false,
      operations: {
        create: this.$t('apiToken.create'),
        read: this.$t('apiToken.read'),
        update: this.$t('apiToken.update'),
        delete: this.$t('apiToken.delete'),
      },
    }
  },
  computed: {
    group() {
      return this.$store.getters['group/get'](this.token.group)
    },
    databases() {
      return this.$store.getters['application/getAllOfGroup'](
        this.group
      ).filter(
        (application) => application.type === DatabaseApplicationType.getType()
      )
    },
  },
  methods: {
    copyTokenToClipboard() {
      copyToClipboard(this.token.key)
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    /**
     * Updates some token properties. If the request fails the changes are going to be
     * reverted.
     */
    async updateToken(token, values, old) {
      Object.assign(token, values)

      try {
        await TokenService(this.$client).update(token.id, values)
      } catch (error) {
        Object.assign(token, old)
        notifyIf(error, 'token')
      }
    },
    /**
     * Asks the backend to rotate the key of the token.
     */
    async rotateKey(token) {
      this.rotateLoading = true

      try {
        const { data } = await TokenService(this.$client).rotateKey(token.id)
        this.token.key = data.key
        this.tokenVisible = true
        this.rotateLoading = false
      } catch (error) {
        this.rotateLoading = false
        notifyIf(error, 'token')
      }
    },
    /**
     * Deletes the token and emits a signal to the parent component such that is can
     * be removed from the list.
     */
    async deleteToken(token) {
      if (this.deleteLoading) {
        return
      }

      try {
        await TokenService(this.$client).delete(token.id)
        this.deleteLoading = false
        this.$emit('deleted')
      } catch (error) {
        this.deleteLoading = false
        notifyIf(error, 'field')
      }
    },
    /**
     * Check if a type (database or table) with the given id exists in the
     * permissions of the provided operation.
     */
    exists(operation, type, id) {
      const permissions = this.token.permissions[operation]
      if (Array.isArray(permissions)) {
        for (const i in permissions) {
          if (permissions[i][0] === type && permissions[i][1] === id) {
            return true
          }
        }
      }
      return false
    },
    /**
     * Adds a type (database or table) to the permissions of the given operation.
     */
    add(operation, type, id) {
      const permissions = this.token.permissions[operation]
      if (!Array.isArray(permissions)) {
        this.token.permissions[operation] = []
      }
      if (!this.exists(operation, type, id)) {
        this.token.permissions[operation].push([type, id])
      }
    },
    /**
     * Removes a type (database or table) to the permissions of the given operation.
     */
    remove(operation, type, id) {
      let permissions = this.token.permissions[operation]
      if (!Array.isArray(permissions)) {
        this.token.permissions[operation] = []
        permissions = []
      }
      this.token.permissions[operation] = permissions.filter((permission) => {
        return !(permission[0] === type && permission[1] === id)
      })
    },
    /**
     * Indicates if the token has permissions to all databases and tables for the given
     * operation. Returns 2 if there is only partially access.
     */
    isActive(operation) {
      const value = this.token.permissions[operation]
      if (value === true) {
        return true
      } else if (
        // If the value is false or if no permissions have been set we can show the
        // switch as if is empty.
        value === false ||
        (Array.isArray(value) && value.length === 0)
      ) {
        return false
      } else {
        return 2
      }
    },
    /**
     * Indicates if the token has permissions to the given database for the given
     * operation. Returns 2 if there is only partially access.
     */
    isDatabaseActive(database, operation) {
      if (
        this.isActive(operation) === true ||
        this.exists(operation, 'database', database.id)
      ) {
        return true
      }
      const tables = database.tables
      for (const i in tables) {
        if (this.exists(operation, 'table', tables[i].id)) {
          return 2
        }
      }
      return false
    },
    /**
     * Indicates if the token has permissions to the given table for the given
     * operation.
     */
    isTableActive(table, database, operation) {
      return (
        this.isActive(operation) === true ||
        this.exists(operation, 'database', database.id) ||
        this.exists(operation, 'table', table.id)
      )
    },
    /**
     * Changes the token permission state of all databases and tables of the given
     * operation. Also updates the permissions with the backend.
     */
    toggle(operation, value) {
      const oldPermissions = JSON.parse(JSON.stringify(this.token.permissions))
      // We can easily change the value to true or false because the permissions are
      // now going to be controlled on global (group) level.
      this.token.permissions[operation] = value
      this.updateToken(
        this.token,
        { permissions: this.token.permissions },
        { permissions: oldPermissions }
      )
    },
    /**
     * Changes the token permission state of a provided database and his tables of the
     * given operation. Also updates the permissions with the backend.
     */
    toggleDatabase(database, sibblings, operation, value) {
      const oldPermissions = JSON.parse(JSON.stringify(this.token.permissions))

      // First we want to add all the databases that already have an active state to
      // the permissions because the permissions are not going to controlled on
      // database level.
      sibblings
        .filter(
          (database) => this.isDatabaseActive(database, operation) === true
        )
        .forEach((database) => {
          this.add(operation, 'database', database.id)
        })

      // Remove all the child table permissions of the database because the
      // permissions are not going to controlled on database level.
      database.tables.forEach((table) => {
        this.remove(operation, 'table', table.id)
      })

      // Depending on the value we either need to remove the database from the list
      // or add it.
      if (value) {
        this.add(operation, 'database', database.id)
      } else {
        this.remove(operation, 'database', database.id)
      }

      // Updates the permissions with the backend.
      this.updateToken(
        this.token,
        { permissions: this.token.permissions },
        { permissions: oldPermissions }
      )
    },
    /**
     * Changes the token permission state of a provided table of the given operation.
     * Also updates the permissions with the backend.
     */
    toggleTable(table, database, databases, operation, value) {
      const oldPermissions = JSON.parse(JSON.stringify(this.token.permissions))

      // First we want to add all the databases that already have an active state to
      // the permissions because the permissions are now going to be controlled on
      // table level.
      databases
        .filter(
          (database) => this.isDatabaseActive(database, operation) === true
        )
        .forEach((database) => {
          this.add(operation, 'database', database.id)
        })

      // We also want to add all the tables that already have an active state to the
      // permissions.
      database.tables
        .filter(
          (table) => this.isTableActive(table, database, operation) === true
        )
        .forEach((table) => {
          this.add(operation, 'table', table.id)
        })

      // Depending on the value we either need to remove the database from the list
      // or add it.
      this.remove(operation, 'database', database.id)
      if (value) {
        this.add(operation, 'table', table.id)
      } else {
        this.remove(operation, 'table', table.id)
      }

      // Updates the permissions with the backend.
      this.updateToken(
        this.token,
        { permissions: this.token.permissions },
        { permissions: oldPermissions }
      )
    },
  },
}
</script>

<i18n>
{
  "en": {
    "apiToken": {
      "create": "create",
      "read": "read",
      "update": "update",
      "delete": "delete",
      "tokenPrefix": "Token:",
      "viewAPIDocs": "View API documentation",
      "generateNewToken": "Generate new token",
      "showOrHide": "Show or hide the token",
      "copyToClipboard": "Copy to clipboard",
      "showDatabases": "show databases"
    }
  },
  "fr": {
    "apiToken": {
      "create": "créer",
      "read": "lire",
      "update": "modifier",
      "delete": "supprimer",
      "tokenPrefix": "Jeton :",
      "viewAPIDocs": "Documentation de l'API",
      "generateNewToken": "Générer un nouveau jeton",
      "showOrHide": "Montrer ou masquer le jeton",
      "copyToClipboard": "Copier dans le presse-papier",
      "showDatabases": "Afficher le détail"
    }
  }
}
</i18n>
