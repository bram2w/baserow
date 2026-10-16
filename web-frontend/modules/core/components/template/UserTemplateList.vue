<template>
  <div class="user-template-list">
    <div
      class="user-template-list__head"
      :class="{ 'user-template-list__head--centered': $slots.head }"
    >
      <slot name="head">
        <div class="user-template-list__head-title">
          {{ $t('userTemplateList.title') }}
        </div>
      </slot>
    </div>
    <div class="user-template-list__body">
      <div v-if="!ready" class="user-template-list__loading">
        <div class="loading"></div>
      </div>
      <TemplateEmptyState
        v-else-if="failed"
        icon="iconoir-warning-triangle"
        :title="$t('userTemplateList.errorTitle')"
        :description="$t('userTemplateList.errorDescription')"
      >
        <Button type="secondary" :loading="loading" @click="refresh()">
          {{ $t('userTemplateList.retry') }}
        </Button>
      </TemplateEmptyState>
      <template v-else-if="isEmpty">
        <div class="user-template-list__title">
          {{ $t('userTemplateList.title') }}
        </div>
        <TemplateEmptyState
          icon="iconoir-box"
          :title="$t('userTemplateList.emptyTitle')"
          :description="
            createDisabledReason || $t('userTemplateList.emptyDescription')
          "
        >
          <Button
            v-if="!createDisabledReason"
            icon="iconoir-plus"
            @click="emit('create')"
          >
            {{ $t('userTemplateList.newTemplate') }}
          </Button>
        </TemplateEmptyState>
      </template>
      <template v-else>
        <div class="user-template-list__toolbar">
          <div class="user-template-list__title">
            {{ $t('userTemplateList.count', { count }) }}
          </div>
          <FormInput
            ref="searchInput"
            v-model="search"
            class="user-template-list__search"
            icon-left="iconoir-search"
            :placeholder="$t('userTemplateList.search')"
          ></FormInput>
          <span v-tooltip="createDisabledReason || null">
            <Button
              icon="iconoir-plus"
              :disabled="!!createDisabledReason"
              @click="emit('create')"
            >
              {{ $t('userTemplateList.newTemplate') }}
            </Button>
          </span>
        </div>
        <TemplateEmptyState
          v-if="templates.length === 0"
          :query="loadedSearch"
        ></TemplateEmptyState>
        <div v-else class="user-template-list__table">
          <div class="user-template-list__row user-template-list__row--head">
            <div class="user-template-list__cell">
              {{ $t('userTemplateList.name') }}
            </div>
            <div class="user-template-list__cell">
              {{ $t('userTemplateList.visibility') }}
            </div>
            <div class="user-template-list__cell">
              {{ $t('userTemplateList.lastUpdated') }}
            </div>
          </div>
          <InfiniteScroll
            class="user-template-list__scroll"
            :current-count="templates.length"
            :max-count="count"
            :page-size="PAGE_SIZE"
            :loading="loading"
            :render-end="false"
            @load-next-page="fetchNextPage"
          >
            <a
              v-for="template in templates"
              :key="template.id"
              class="user-template-list__row"
              role="button"
              tabindex="0"
              @click="emit('selected', template)"
              @keydown.enter.prevent="emit('selected', template)"
              @keydown.space.prevent="emit('selected', template)"
            >
              <div class="user-template-list__cell user-template-list__name">
                <div class="user-template-list__icon">
                  <i :class="template.icon || 'iconoir-view-grid'"></i>
                </div>
                <div class="user-template-list__name-text">
                  <div class="user-template-list__name-title">
                    {{ template.name }}
                  </div>
                  <div
                    v-if="template.description"
                    class="user-template-list__description"
                  >
                    {{ template.description }}
                  </div>
                </div>
              </div>
              <div class="user-template-list__cell">
                <Badge
                  v-tooltip="template.reason || null"
                  :color="getState(template).color"
                  rounded
                  >{{ getState(template).label }}</Badge
                >
              </div>
              <div class="user-template-list__cell user-template-list__updated">
                {{ getHumanAgoLabel($i18n.t, template.updated_on) }}
              </div>
            </a>
          </InfiniteScroll>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useNuxtApp } from '#app'
import debounce from 'lodash/debounce'

import TemplateService from '@baserow/modules/core/services/template'
import { getHumanAgoLabel } from '@baserow/modules/core/utils/date'
import { notifyIf } from '@baserow/modules/core/utils/error'
import InfiniteScroll from '@baserow/modules/core/components/helpers/InfiniteScroll'
import TemplateEmptyState from '@baserow/modules/core/components/template/TemplateEmptyState'

const PAGE_SIZE = 20

const STATES = {
  private: { color: 'neutral', label: 'userTemplateList.statePrivate' },
  in_review: { color: 'yellow', label: 'userTemplateList.stateInReview' },
  rejected: { color: 'red', label: 'userTemplateList.stateRejected' },
  blocked: { color: 'red', label: 'userTemplateList.stateBlocked' },
  public: { color: 'green', label: 'userTemplateList.statePublic' },
}

/**
 * A state that this version doesn't know is shown as it is, so that the list
 * still works when a new state is added.
 */
function getState(template) {
  const state = STATES[template.state]
  return state
    ? { color: state.color, label: $i18n.t(state.label) }
    : { color: 'neutral', label: template.state }
}

const props = defineProps({
  // Whether the list is shown. A hidden list must not claim the search shortcut,
  // because only the listener with the highest priority receives it.
  active: {
    type: Boolean,
    required: false,
    default: true,
  },
})

const emit = defineEmits(['selected', 'create'])

const { $client, $i18n, $priorityBus, $store, $hasPermission } = useNuxtApp()

const searchInput = ref(null)
const search = ref('')
const templates = ref([])
const count = ref(0)
const loading = ref(false)
const loaded = ref(false)
// Whether the templates couldn't be loaded, while none are shown yet.
const failed = ref(false)
const permissionsLoaded = ref(false)
// The search the shown templates were loaded with.
const loadedSearch = ref('')

// Only the response of the latest request is used, so that a slow response of an
// older search can't replace the results of the current one.
let lastRequest = 0

// Nothing found without a search: the user hasn't created any template yet.
const isEmpty = computed(() => count.value === 0 && loadedSearch.value === '')

// Shown once both are loaded, so that the layout doesn't change right after.
const ready = computed(() => loaded.value && permissionsLoaded.value)

const workspaces = computed(() => $store.getters['workspace/getAll'])

// A template is created from a workspace that the user can export. Explains why
// the user can't create one, or is null when they can.
const createDisabledReason = computed(() => {
  if (workspaces.value.length === 0) {
    return $i18n.t('userTemplateList.noWorkspace')
  }
  const canExport = workspaces.value.some((workspace) =>
    $hasPermission('workspace.export', workspace, workspace.id)
  )
  return canExport ? null : $i18n.t('userTemplateList.noPermission')
})

/**
 * The permissions of a workspace are only fetched when needed. Until then the
 * global permissions are used, which can allow an export that isn't allowed.
 */
async function loadPermissions() {
  await Promise.all(
    workspaces.value.map((workspace) =>
      $store.dispatch('workspace/fetchPermissions', workspace).catch(() => {})
    )
  )
  permissionsLoaded.value = true
}

async function fetchPage(offset, requestSearch = search.value) {
  const request = ++lastRequest
  loading.value = true
  try {
    const { data } = await TemplateService($client).fetchOwn({
      offset,
      limit: PAGE_SIZE,
      search: requestSearch,
    })
    if (request !== lastRequest) {
      return
    }
    templates.value =
      offset === 0 ? data.results : [...templates.value, ...data.results]
    count.value = data.count
    loadedSearch.value = requestSearch
    failed.value = false
  } catch (error) {
    if (request === lastRequest) {
      notifyIf(error, 'templates')
      failed.value = failed.value || !loaded.value
    }
  } finally {
    if (request === lastRequest) {
      loaded.value = true
      loading.value = false
    }
  }
}

function fetchNextPage() {
  return fetchPage(templates.value.length, loadedSearch.value)
}

/**
 * Loads the first page again, for example after a template was created.
 */
function refresh() {
  return fetchPage(0)
}

const searchChanged = debounce(() => fetchPage(0), 300)

watch(search, searchChanged)

function searchStarted({ event }) {
  event.preventDefault()
  searchInput.value?.focus()
}

function listenToSearch(active) {
  $priorityBus.$off('start-search', searchStarted)
  if (active) {
    $priorityBus.$on('start-search', $priorityBus.level.HIGH, searchStarted)
  }
}

onMounted(() => {
  fetchPage(0)
  loadPermissions()
  listenToSearch(props.active)
})
watch(() => props.active, listenToSearch)

onBeforeUnmount(() => {
  searchChanged.cancel()
  $priorityBus.$off('start-search', searchStarted)
})

defineExpose({ refresh })
</script>
