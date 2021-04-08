import Vuelidate from 'vuelidate'
import Vue from 'vue'
import Vuex from 'vuex'

const addVuex = (context) => {
  context.vuex = Vuex
  context.vue.use(context.vuex)
}
const addVuelidate = (context) => {
  context.vuelidate = Vuelidate
  context.vue.use(context.vuelidate)
}
const addBus = (context) => {
  context.vue_bus = Vue
  const EventBus = new Vue()

  const EventBusPlugin = {
    install(v) {
      // Event bus
      v.prototype.$bus = EventBus
    },
  }
  context.vue.use(EventBusPlugin)
}
const compositeConfiguration = (...configs) => {
  return (context) => configs.forEach((config) => config(context))
}

export const bootstrapVueContext = (configureContext) => {
  configureContext =
    configureContext || compositeConfiguration(addVuex, addVuelidate, addBus)

  const context = {}
  const teardownVueContext = () => {
    jest.resetModules()
  }

  jest.isolateModules(() => {
    context.vueTestUtils = require('@vue/test-utils')
    context.vueTestUtils.config.stubs.nuxt = { template: '<div />' }
    context.vueTestUtils.config.stubs['nuxt-link'] = {
      template: '<a><slot /></a>',
    }
    context.vueTestUtils.config.stubs['no-ssr'] = {
      template: '<span><slot /></span>',
    }
    context.vue = context.vueTestUtils.createLocalVue()

    jest.doMock('vue', () => context.vue)

    configureContext && configureContext(context)
  })

  return {
    teardownVueContext,
    ...context,
  }
}
