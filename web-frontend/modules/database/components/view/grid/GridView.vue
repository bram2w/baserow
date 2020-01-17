<template>
  <div class="grid-view">
    <div class="grid-view-left" style="width: 260px;">
      <div class="grid-view-inner" style="width: 260px;">
        <div class="grid-view-head">
          <div class="grid-view-column" style="width: 60px;"></div>
          <GridViewField
            v-if="primary !== null"
            :field="primary"
          ></GridViewField>
        </div>
        <div class="grid-view-body"></div>
        <div class="grid-view-foot">
          <div class="grid-view-column">
            <div class="grid-view-foot-info">@TODO</div>
          </div>
        </div>
      </div>
    </div>
    <div class="grid-view-divider" style="left: 260px;"></div>
    <div class="grid-view-right" style="left: 260px;">
      <div
        class="grid-view-inner"
        :style="{ 'min-width': 100 + fields.length * 200 + 'px' }"
      >
        <div class="grid-view-head">
          <GridViewField
            v-for="field in fields"
            :key="field.id"
            :field="field"
          ></GridViewField>
          <div class="grid-view-column" style="width: 100px;">
            <a
              ref="createFieldContextLink"
              class="grid-view-add-column"
              @click="
                $refs.createFieldContext.toggle($refs.createFieldContextLink)
              "
            >
              <i class="fas fa-plus"></i>
            </a>
            <CreateFieldContext
              ref="createFieldContext"
              :table="table"
            ></CreateFieldContext>
          </div>
        </div>
        <div class="grid-view-body"></div>
        <div class="grid-view-foot"></div>
      </div>
    </div>
  </div>
</template>

<script>
import CreateFieldContext from '@/modules/database/components/field/CreateFieldContext'
import GridViewField from '@/modules/database/components/view/grid/GridViewField'

export default {
  name: 'GridView',
  components: {
    CreateFieldContext,
    GridViewField
  },
  props: {
    primary: {
      type: Object,
      required: true
    },
    fields: {
      type: Array,
      required: true
    },
    view: {
      type: Object,
      required: true
    },
    table: {
      type: Object,
      required: true
    },
    database: {
      type: Object,
      required: true
    }
  }
}
</script>
