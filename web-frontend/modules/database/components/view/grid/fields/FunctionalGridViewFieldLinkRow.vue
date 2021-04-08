<template functional>
  <div class="grid-view__cell grid-field-link-row__cell">
    <div class="grid-field-link-row__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="grid-field-link-row__item"
      >
        <span
          class="grid-field-link-row__name"
          :class="{
            'grid-field-link-row__name--unnamed':
              item.value === null || item.value === '',
          }"
        >
          {{ item.value || 'unnamed row ' + item.id }}
        </span>
      </div>
    </div>
  </div>
</template>
