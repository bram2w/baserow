import { notifyIf } from '@baserow/modules/core/utils/error'

/**
 * Switches for the built-in tools (workspace access, web search), which are
 * on when their tool row exists. Expects `application`, `tools` and the agent
 * context's `storePrefix` on the component.
 */
export default {
  data() {
    return {
      // Desired state per built-in tool type while its create/delete request
      // is being synced; the switch shows this intent instead of the store
      // state so toggling is optimistic and never blocks.
      pendingBuiltIn: {},
    }
  },
  computed: {
    canToggleBuiltInTools() {
      // Toggling a built-in tool either creates or deletes its row.
      return ['create_tool', 'delete_tool'].every((operation) =>
        this.hasAgentPermission(
          `agent_application.${operation}`,
          this.application,
          this.application.workspace.id
        )
      )
    },
  },
  methods: {
    hasBuiltInTool(type) {
      return this.tools.some((tool) => tool.type === type)
    },
    builtInToolValue(type) {
      return type in this.pendingBuiltIn
        ? this.pendingBuiltIn[type]
        : this.hasBuiltInTool(type)
    },
    async toggleBuiltInTool(type, enabled) {
      const syncing = type in this.pendingBuiltIn
      this.pendingBuiltIn[type] = enabled
      if (syncing) {
        // The running sync loop below picks up the latest intent.
        return
      }
      try {
        // Sync until the store matches the latest intent, so rapid toggling
        // serializes into follow-up requests instead of racing a create
        // against a delete.
        while (this.pendingBuiltIn[type] !== this.hasBuiltInTool(type)) {
          if (this.pendingBuiltIn[type]) {
            await this.$store.dispatch(
              `${this.storePrefix}agentApplication/createTool`,
              {
                applicationId: this.application.id,
                values: { type },
              }
            )
          } else {
            const tool = this.tools.find((t) => t.type === type)
            if (!tool) {
              break
            }
            await this.$store.dispatch(
              `${this.storePrefix}agentApplication/deleteTool`,
              { toolId: tool.id }
            )
          }
        }
      } catch (error) {
        // Dropping the pending intent reverts the switch to the store state.
        notifyIf(error, 'application')
      } finally {
        delete this.pendingBuiltIn[type]
      }
    },
  },
}
