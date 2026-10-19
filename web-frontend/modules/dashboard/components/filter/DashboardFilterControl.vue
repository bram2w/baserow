<template>
  <div
    class="dashboard-filter"
    :class="{ 'dashboard-filter--selected': selected }"
  >
    <label class="dashboard-filter__label" :for="controlId">{{
      filter.label
    }}</label>
    <div
      class="dashboard-filter__control"
      :class="{ 'dashboard-filter__control--active': appliedValues.length }"
    >
      <button
        :id="controlId"
        ref="trigger"
        class="dashboard-filter__trigger"
        type="button"
        :aria-expanded="opened"
        @click="activate"
      >
        <i class="iconoir-filter" aria-hidden="true"></i>
        <span class="dashboard-filter__value">{{
          appliedValues.length > 1
            ? $t('dashboardFilter.selections', { count: appliedValues.length })
            : appliedValues[0] || $t('dashboardFilter.choose')
        }}</span>
        <i
          v-if="hasUnavailable"
          v-tooltip="$t('dashboardFilter.unavailableHelp')"
          class="iconoir-info-circle dashboard-filter__info"
          :aria-label="$t('dashboardFilter.unavailable')"
        ></i>
      </button>
      <button
        v-if="editMode"
        class="dashboard-filter__action"
        type="button"
        :aria-label="$t('dashboardFilter.settings')"
        @click="$emit('select')"
      >
        <i class="iconoir-more-vert" aria-hidden="true"></i>
      </button>
      <button
        v-else-if="appliedValues.length"
        class="dashboard-filter__action"
        type="button"
        :aria-label="$t('dashboardFilter.clear')"
        @click="$emit('apply', [])"
      >
        <i class="iconoir-cancel" aria-hidden="true"></i>
      </button>
      <i
        v-else
        class="iconoir-nav-arrow-down dashboard-filter__arrow"
        aria-hidden="true"
      ></i>
    </div>
    <Context
      ref="context"
      class="dashboard-filter__context"
      @shown="onShown"
      @hidden="onHidden"
    >
      <form @submit.prevent="apply" @keydown.esc.stop.prevent="close">
        <template v-if="filter.mode === 'dropdown'">
          <div class="dashboard-filter__search">
            <FormInput
              v-model="search"
              :placeholder="$t('action.search')"
              icon-left="iconoir-search"
              :aria-label="$t('action.search')"
              @update:model-value="searchOptions"
            />
          </div>
          <div class="dashboard-filter__operator">
            {{ $t(`dashboardFilter.${filter.operator}`) }}...
          </div>
          <div class="dashboard-filter__choices">
            <div
              v-for="value in displayedOptions"
              :key="value"
              class="dashboard-filter__choice"
            >
              <Checkbox
                :model-value="draft.includes(value)"
                @update:model-value="toggle(value, $event)"
              >
                <span class="dashboard-filter__option-value">{{ value }}</span>
                <span
                  v-if="optionState.unavailable.includes(value)"
                  v-tooltip="$t('dashboardFilter.unavailableHelp')"
                  class="dashboard-filter__unavailable"
                  >{{ $t('dashboardFilter.unavailable') }}</span
                >
              </Checkbox>
            </div>
            <div
              v-if="optionState.loading"
              class="dashboard-filter__message"
              role="status"
            >
              {{ $t('dashboardFilter.loading') }}
            </div>
            <div
              v-else-if="optionState.error"
              class="dashboard-filter__message"
              role="status"
            >
              {{ $t('dashboardFilter.optionsError') }}
              <Button type="secondary" size="small" @click="requestOptions()">{{
                $t('action.retry')
              }}</Button>
            </div>
            <div
              v-else-if="!displayedOptions.length"
              class="dashboard-filter__message"
            >
              {{ $t('dashboardFilter.noOptions') }}
            </div>
            <Button
              v-if="optionState.next && !optionState.loading"
              type="secondary"
              size="small"
              class="dashboard-filter__more"
              @click="requestOptions(true)"
              >{{ $t('dashboardFilter.more') }}</Button
            >
          </div>
        </template>
        <div v-else class="dashboard-filter__input">
          <FormGroup
            :label="`${$t(`dashboardFilter.${filter.operator}`)}...`"
            small-label
          >
            <FormInput
              ref="input"
              :model-value="draft[0] || ''"
              :placeholder="$t('dashboardFilter.inputPlaceholder')"
              :maxlength="10000"
              @update:model-value="draft = [$event]"
            />
          </FormGroup>
        </div>
        <div class="dashboard-filter__footer">
          <Button :disabled="!changed" button-type="submit">{{
            $t(
              appliedValues.length
                ? 'dashboardFilter.update'
                : 'dashboardFilter.apply'
            )
          }}</Button>
        </div>
      </form>
    </Context>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, useId } from 'vue'
import debounce from 'lodash/debounce'
import Context from '@baserow/modules/core/components/Context'
import Checkbox from '@baserow/modules/core/components/Checkbox'
import FormInput from '@baserow/modules/core/components/FormInput'
import FormGroup from '@baserow/modules/core/components/FormGroup'
import Button from '@baserow/modules/core/components/Button'

const props = defineProps({
  filter: { type: Object, required: true },
  appliedValues: { type: Array, default: () => [] },
  optionState: {
    type: Object,
    default: () => ({
      results: [],
      unavailable: [],
      next: null,
      loading: false,
      error: false,
    }),
  },
  editMode: Boolean,
  selected: Boolean,
})
const emit = defineEmits(['apply', 'select', 'options'])
const controlId = `dashboard-filter-${useId()}`
const context = ref(null)
const trigger = ref(null)
const input = ref(null)
const opened = ref(false)
const draft = ref([])
const search = ref('')
const normalizedDraft = computed(() =>
  props.filter.mode === 'input'
    ? draft.value.map((value) => value.trim()).filter(Boolean)
    : draft.value
)
const changed = computed(
  () =>
    JSON.stringify(normalizedDraft.value) !==
    JSON.stringify(props.appliedValues)
)
const displayedOptions = computed(() => [
  ...new Set([...draft.value, ...props.optionState.results]),
])
const hasUnavailable = computed(() =>
  props.appliedValues.some((value) =>
    props.optionState.unavailable.includes(value)
  )
)
const requestOptions = (more = false) =>
  emit('options', {
    search: search.value,
    more,
    selected: [...new Set([...props.appliedValues, ...draft.value])],
  })
const searchOptions = debounce(() => {
  if (opened.value) requestOptions()
}, 250)

function activate() {
  if (props.editMode) emit('select')
  else context.value.toggle(trigger.value, 'bottom', 'left', 4)
}
async function onShown() {
  opened.value = true
  draft.value = [...props.appliedValues]
  search.value = ''
  if (props.filter.mode === 'dropdown') requestOptions()
  await nextTick()
  input.value?.focus()
}
function onHidden() {
  opened.value = false
  searchOptions.cancel()
  draft.value = [...props.appliedValues]
}
function toggle(value, checked) {
  draft.value = checked
    ? props.filter.multiple
      ? [...draft.value, value]
      : [value]
    : draft.value.filter((item) => item !== value)
}
function apply() {
  if (!changed.value) return
  emit('apply', [...normalizedDraft.value])
  close()
}
function close() {
  context.value.hide()
  trigger.value?.focus()
}
onBeforeUnmount(() => searchOptions.cancel())
</script>
