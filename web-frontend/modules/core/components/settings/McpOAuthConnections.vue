<template>
  <div v-if="oauthEnabled" class="mcp-oauth-connections">
    <h3 class="mcp-oauth-connections__title">
      {{ $t('mcpOAuthConnections.title') }}
    </h3>
    <p class="mcp-oauth-connections__description">
      {{ $t('mcpOAuthConnections.description') }}
    </p>
    <div class="mcp-oauth-connections__url margin-bottom-1">
      <div class="mcp-oauth-connections__url-box" data-test="mcp-oauth-url">
        {{ mcpUrl }}
      </div>
      <a
        v-tooltip="$t('mcpOAuthConnections.copyURL')"
        class="mcp-oauth-connections__url-copy"
        @click="copyUrl"
      >
        <i class="iconoir-copy" />
        <Copied ref="copied"></Copied>
      </a>
    </div>
    <Tabs header-no-padding content-no-x-padding>
      <Tab title="Claude">
        <MarkdownIt
          class="mcp-oauth-connections__instructions"
          :content="$t('mcpOAuthConnections.claudeInstructions')"
        ></MarkdownIt>
      </Tab>
      <Tab title="Claude Code">
        <MarkdownIt
          class="mcp-oauth-connections__instructions margin-bottom-1"
          :content="$t('mcpOAuthConnections.claudeCodeInstructions')"
        ></MarkdownIt>
        <pre><code class="mcp-oauth-connections__code">claude mcp add --transport http baserow {{ mcpUrl }}</code></pre>
      </Tab>
      <Tab title="ChatGPT">
        <MarkdownIt
          class="mcp-oauth-connections__instructions"
          :content="$t('mcpOAuthConnections.chatGptInstructions')"
        ></MarkdownIt>
      </Tab>
      <Tab title="Cursor">
        <MarkdownIt
          class="mcp-oauth-connections__instructions margin-bottom-1"
          :content="$t('mcpOAuthConnections.cursorInstructions')"
        ></MarkdownIt>
        <pre><code class="mcp-oauth-connections__code">{
  "mcpServers": {
    "baserow": {
      "url": "{{ mcpUrl }}"
    }
  }
}</code></pre>
      </Tab>
    </Tabs>
    <h3 class="mcp-oauth-connections__title">
      {{ $t('mcpOAuthConnections.connectedApps') }}
    </h3>
    <p
      v-if="!connections.length"
      class="mcp-oauth-connections__empty"
      data-test="mcp-oauth-empty"
    >
      {{ $t('mcpOAuthConnections.noConnections') }}
    </p>
    <div
      v-for="connection in connections"
      :key="connection.id"
      class="mcp-oauth-connections__item"
      :data-test="`mcp-oauth-connection-${connection.id}`"
    >
      <div class="mcp-oauth-connections__avatar">
        {{ initial(connection.client_name) }}
      </div>
      <div class="mcp-oauth-connections__info">
        <div class="mcp-oauth-connections__name">
          <span class="mcp-oauth-connections__client">{{
            connection.client_name
          }}</span>
          <Badge
            v-if="connection.verified"
            size="small"
            data-test="mcp-oauth-published"
            >{{
              $t('mcpOAuthConnections.publishedBy', {
                host: connection.verified_host,
              })
            }}</Badge
          >
          <Badge
            v-if="connection.expired"
            v-tooltip="$t('mcpOAuthConnections.expiredTooltip')"
            color="yellow"
            size="small"
            data-test="mcp-oauth-expired"
            >{{ $t('mcpOAuthConnections.expired') }}</Badge
          >
        </div>
        <div class="mcp-oauth-connections__meta">
          {{ connection.workspace_name }} ·
          {{ toolCount(connection.tool_count) }} ·
          {{ connectedOn(connection.created) }}
        </div>
        <div
          v-if="toolsOff(connection) > 0"
          class="mcp-oauth-connections__tools-off"
          data-test="mcp-oauth-tools-off"
        >
          {{
            $t('mcpOAuthConnections.toolsOff', {
              count: toolsOff(connection),
            })
          }}
        </div>
      </div>
      <Button
        type="secondary"
        size="small"
        data-test="mcp-oauth-edit-tools"
        @click="editTools(connection)"
        >{{ $t('mcpOAuthConnections.editTools') }}</Button
      >
      <Button
        type="secondary"
        size="small"
        :loading="disconnecting === connection.id"
        :disabled="disconnecting === connection.id"
        data-test="mcp-oauth-disconnect"
        @click="disconnect(connection)"
        >{{
          confirming === connection.id
            ? $t('mcpOAuthConnections.confirmDisconnect')
            : $t('mcpOAuthConnections.disconnect')
        }}</Button
      >
    </div>
    <Modal ref="toolsModal" small @hidden="editing = null">
      <template v-if="editing" #content>
        <h2 class="box__title">
          {{
            $t('mcpOAuthConnections.editToolsTitle', {
              client: editing.client_name,
            })
          }}
        </h2>
        <p class="mcp-oauth-connections__modal-description">
          {{
            $t('mcpOAuthConnections.editToolsDescription', {
              workspace: editing.workspace_name,
            })
          }}
        </p>
        <McpToolPicker
          v-model="pickedTools"
          :tools="tools"
          :groups="groups"
          :unavailable="editing.unavailable_tools"
        />
        <div class="mcp-oauth-connections__modal-actions">
          <Button type="secondary" @click="toolsModal.hide()">{{
            $t('action.cancel')
          }}</Button>
          <Button
            type="primary"
            :loading="savingTools"
            :disabled="savingTools || !pickedTools.length"
            data-test="mcp-oauth-save-tools"
            @click="saveTools"
            >{{ $t('mcpOAuthConnections.saveTools') }}</Button
          >
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import McpToolPicker from '@baserow/modules/core/components/mcp/McpToolPicker'
import moment from '@baserow/modules/core/moment'
import MCPOAuthService from '@baserow/modules/core/services/mcpOAuth'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

const emit = defineEmits(['loaded'])

const { $client } = useNuxtApp()
const { t } = useI18n()

const oauthEnabled = ref(false)
const mcpUrl = ref('')
const connections = ref([])
// Every tool a connection can be given, and their groups.
const tools = ref([])
const groups = ref([])
const toolsModal = ref(null)
// The connection whose tools are being edited.
const editing = ref(null)
const pickedTools = ref([])
const savingTools = ref(false)
const confirming = ref(null)
const disconnecting = ref(null)
const copied = ref(null)

onMounted(async () => {
  try {
    const { data } = await MCPOAuthService($client).fetchConnections()
    oauthEnabled.value = data.oauth_enabled
    mcpUrl.value = data.mcp_url
    connections.value = data.connections
    tools.value = data.tools || []
    groups.value = data.groups || []
  } catch (error) {
    notifyIf(error)
  }
  emit('loaded', oauthEnabled.value)
})

function initial(name) {
  return (name || '').trim().charAt(0).toUpperCase()
}

function toolCount(count) {
  return t('mcpOAuthConnections.tools', { count })
}

function connectedOn(created) {
  return t('mcpOAuthConnections.connectedOn', {
    date: moment.utc(created).local().format('L'),
  })
}

// Tools the connection could use but doesn't have. New tools are never turned on
// for an existing connection, so this is where the user finds them.
function toolsOff(connection) {
  const unavailable = new Set(connection.unavailable_tools || [])
  const allowed = new Set(connection.allowed_tools || [])
  return tools.value.filter(
    (tool) => !unavailable.has(tool.name) && !allowed.has(tool.name)
  ).length
}

function editTools(connection) {
  editing.value = connection
  pickedTools.value = tools.value
    .map((tool) => tool.name)
    .filter((name) => (connection.allowed_tools || []).includes(name))
  toolsModal.value.show()
}

async function saveTools() {
  savingTools.value = true
  try {
    const { data } = await MCPOAuthService($client).updateTools(
      editing.value.id,
      pickedTools.value
    )
    connections.value = connections.value.map((c) =>
      c.id === data.id ? data : c
    )
    toolsModal.value.hide()
  } catch (error) {
    notifyIf(error)
  }
  savingTools.value = false
}

function copyUrl() {
  copyToClipboard(mcpUrl.value)
  copied.value.show()
}

/**
 * The first click asks for confirmation, the second one deletes the grant,
 * which also revokes the app's tokens.
 */
async function disconnect(connection) {
  if (confirming.value !== connection.id) {
    confirming.value = connection.id
    return
  }
  disconnecting.value = connection.id
  try {
    await MCPOAuthService($client).disconnect(connection.id)
    connections.value = connections.value.filter((c) => c.id !== connection.id)
  } catch (error) {
    notifyIf(error)
  }
  confirming.value = null
  disconnecting.value = null
}
</script>
