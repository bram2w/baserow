<template>
  <span
    class="agent-usage-summary"
    :class="{ 'agent-usage-summary--stacked': stacked }"
  >
    <span
      class="agent-usage-summary__part"
      :title="
        cached > 0
          ? $t('agentUsage.inputCachedTitle', {
              input: input.toLocaleString(),
              cached: cached.toLocaleString(),
            })
          : $t('agentUsage.inputTitle', { input: input.toLocaleString() })
      "
    >
      {{ $t('agentUsage.input', { tokens: formatTokens(input) }) }}
      <template v-if="cached > 0">
        {{ $t('agentUsage.cached', { tokens: formatTokens(cached) }) }}
      </template>
    </span>
    <span
      class="agent-usage-summary__part"
      :title="$t('agentUsage.outputTitle', { output: output.toLocaleString() })"
    >
      {{ $t('agentUsage.output', { tokens: formatTokens(output) }) }}
    </span>
    <span v-if="hasCost(usage)" class="agent-usage-summary__part">
      {{ formatCost(usage.cost ?? usage.total_cost) }}
    </span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import {
  cachedInputTokens,
  formatCost,
  formatTokens,
  hasCost,
  inputTokens,
  outputTokens,
} from '@baserow_enterprise/utils/agentUsage'

/**
 * Input and output side by side, never summed: every step re-sends the
 * conversation, so input dwarfs output, and the two are priced differently.
 * The cached part of the input explains why a lot of input can cost little.
 */
const props = defineProps({
  usage: {
    type: Object,
    required: true,
  },
  // One part per line, for narrow places like a context menu.
  stacked: {
    type: Boolean,
    required: false,
    default: false,
  },
})

const input = computed(() => inputTokens(props.usage))
const cached = computed(() => cachedInputTokens(props.usage))
const output = computed(() => outputTokens(props.usage))
</script>
