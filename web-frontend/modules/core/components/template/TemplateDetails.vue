<template>
  <TemplatePreview
    :template="template"
    :sidebar-width="320"
    class="template-details"
  >
    <template #sidebar="{ applications, page, selectPage, selectApplication }">
      <div class="template-details__sidebar">
        <div v-if="showBack" class="template-details__back">
          <a
            class="template-details__back-link"
            role="button"
            tabindex="0"
            @click="emit('back')"
            @keydown.enter.prevent="emit('back')"
            @keydown.space.prevent="emit('back')"
          >
            <i class="iconoir-nav-arrow-left"></i>
            {{ $t('templateDetails.back') }}
          </a>
        </div>
        <div class="template-details__info">
          <div class="template-details__title">
            <div class="template-details__icon">
              <i :class="template.icon || 'iconoir-view-grid'"></i>
            </div>
            <div class="template-details__name">{{ template.name }}</div>
          </div>
          <div
            v-if="template.description"
            class="template-details__description"
          >
            {{ template.description }}
          </div>
          <div v-if="categories.length" class="template-details__categories">
            <span
              v-for="category in categories"
              :key="category.id"
              class="template-details__category"
              >{{ category.name }}</span
            >
          </div>
        </div>
        <div class="template-details__contents">
          <div class="template-details__contents-title">
            {{ $t('templateDetails.contents') }}
          </div>
          <ul class="tree">
            <component
              :is="getApplicationComponent(application)"
              v-for="application in sortApplications(applications)"
              :key="application.id"
              :application="application"
              :page="page"
              @selected="selectApplication"
              @selected-page="selectPage"
            ></component>
          </ul>
        </div>
        <div
          v-if="isOwn"
          class="template-details__foot template-details__own-actions"
        >
          <ButtonIcon
            ref="moreButton"
            type="secondary"
            icon="iconoir-more-vert"
            :title="$t('templateDetails.actions')"
            @click="contextRef.toggle(moreButton.$el, 'top', 'right', 4)"
          ></ButtonIcon>
          <Context ref="contextRef">
            <ul class="context__menu">
              <li class="context__menu-item">
                <a
                  class="context__menu-item-link"
                  @click.prevent="edit('details')"
                >
                  <i class="context__menu-item-icon iconoir-edit-pencil"></i>
                  {{ $t('templateDetails.editDetails') }}
                </a>
              </li>
              <li class="context__menu-item">
                <a
                  class="context__menu-item-link"
                  @click.prevent="edit('content')"
                >
                  <i class="context__menu-item-icon iconoir-refresh-double"></i>
                  {{ $t('templateDetails.updateContent') }}
                </a>
              </li>
              <li class="context__menu-item context__menu-item--with-separator">
                <a
                  class="context__menu-item-link context__menu-item-link--delete"
                  @click.prevent="askToDelete()"
                >
                  <i class="context__menu-item-icon iconoir-bin"></i>
                  {{ $t('templateDetails.delete') }}
                </a>
              </li>
            </ul>
          </Context>
        </div>
        <div
          v-else-if="template.type !== 'user'"
          class="template-details__foot"
        >
          <TemplateInstall
            :template="template"
            :workspace="workspace"
            @installed="emit('installed')"
          ></TemplateInstall>
        </div>
      </div>
    </template>
  </TemplatePreview>
</template>

<script setup>
import { ref } from 'vue'
import { useNuxtApp } from '#app'

import TemplatePreview from '@baserow/modules/core/components/template/TemplatePreview'
import TemplateInstall from '@baserow/modules/core/components/template/TemplateInstall'

const props = defineProps({
  template: {
    type: Object,
    required: true,
  },
  // The categories the template is listed in.
  categories: {
    type: Array,
    required: false,
    default: () => [],
  },
  // The workspace the template is installed into by default.
  workspace: {
    type: Object,
    required: false,
    default: null,
  },
  showBack: {
    type: Boolean,
    required: false,
    default: false,
  },
  // Whether the template is one of the user's, who can then update it.
  isOwn: {
    type: Boolean,
    required: false,
    default: false,
  },
})

// `edit` asks to update the details or the content of the user's template, and
// `delete` to delete it.
const emit = defineEmits(['back', 'installed', 'edit', 'delete'])

const { $registry } = useNuxtApp()

const moreButton = ref(null)
const contextRef = ref(null)

function edit(mode) {
  contextRef.value.hide()
  emit('edit', mode)
}

function askToDelete() {
  contextRef.value.hide()
  emit('delete', props.template)
}

function sortApplications(applications) {
  return [...applications].sort((a, b) => a.order - b.order)
}

function getApplicationComponent(application) {
  return $registry
    .get('application', application.type)
    .getTemplateSidebarComponent()
}
</script>
