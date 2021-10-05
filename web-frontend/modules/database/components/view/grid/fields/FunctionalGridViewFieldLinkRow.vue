<template functional>
  <div class="grid-view__cell grid-field-many-to-many__cell">
    <div class="grid-field-many-to-many__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="grid-field-many-to-many__item"
      >
        <span
          class="grid-field-many-to-many__name"
          :class="{
            'grid-field-link-row__unnamed':
              item.value === null || item.value === '',
          }"
        >
          {{ item.value || 'unnamed row ' + item.id }}
        </span>
      </div>
    </div>
  </div>
</template>
