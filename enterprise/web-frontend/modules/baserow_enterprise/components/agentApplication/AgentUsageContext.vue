<template>
  <Context ref="context" class="agent-usage">
    <div class="agent-usage__title">{{ $t('agentUsage.title') }}</div>
    <table class="agent-usage__table">
      <thead>
        <tr>
          <th class="agent-usage__heading"></th>
          <th class="agent-usage__heading agent-usage__number">
            {{ $t('agentUsage.inputColumn') }}
          </th>
          <th class="agent-usage__heading agent-usage__number">
            {{ $t('agentUsage.outputColumn') }}
          </th>
          <th class="agent-usage__heading agent-usage__number">
            {{ $t('agentUsage.cost') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="period in periods" :key="period">
          <td class="agent-usage__cell">{{ $t(`agentUsage.${period}`) }}</td>
          <td
            class="agent-usage__cell agent-usage__number"
            :title="
              $t('agentUsage.inputCachedTitle', {
                input: usage[period].input_tokens.toLocaleString(),
                cached: usage[period].cached_input_tokens.toLocaleString(),
              })
            "
          >
            {{ formatTokens(usage[period].input_tokens) }}
            <template v-if="usage[period].cached_input_tokens > 0">
              {{
                $t('agentUsage.cached', {
                  tokens: formatTokens(usage[period].cached_input_tokens),
                })
              }}
            </template>
          </td>
          <td
            class="agent-usage__cell agent-usage__number"
            :title="usage[period].output_tokens.toLocaleString()"
          >
            {{ formatTokens(usage[period].output_tokens) }}
          </td>
          <td class="agent-usage__cell agent-usage__number">
            <template v-if="usage[period].turns === 0">–</template>
            <template v-else-if="usage[period].unpriced_turns === 0">
              {{ formatCost(usage[period].cost) }}
            </template>
            <span
              v-else-if="hasCost(usage[period])"
              :title="
                $t('agentUsage.partlyUnpriced', {
                  count: usage[period].unpriced_turns,
                })
              "
            >
              {{ formatCost(usage[period].cost) }}
            </span>
            <span v-else :title="$t('agentUsage.unpriced')">–</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="agent-usage__footnote">{{ $t('agentUsage.footnote') }}</div>
  </Context>
</template>

<script setup>
import { ref } from 'vue'
import {
  formatCost,
  formatTokens,
  hasCost,
} from '@baserow_enterprise/utils/agentUsage'

defineProps({
  usage: {
    type: Object,
    required: true,
  },
})

const periods = ['today', 'week', 'month', 'lifetime']

const context = ref(null)
const toggle = (...args) => context.value.toggle(...args)

defineExpose({ toggle })
</script>
