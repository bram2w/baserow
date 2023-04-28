import Vue from 'vue'
import { config } from '@vue/test-utils'

Vue.config.silent = true

// Mock Nuxt components
config.stubs.nuxt = { template: '<div />' }
config.stubs['nuxt-link'] = { template: '<a><slot /></a>' }
config.stubs['no-ssr'] = { template: '<span><slot /></span>' }

function fail(message = '') {
  let failMessage = ''
  failMessage += '\n'
  failMessage += 'FAIL FUNCTION TRIGGERED\n'
  failMessage += 'The fail function has been triggered'
  failMessage += message ? ' with message:' : ''

  expect(message).toEqual(failMessage)
}
global.fail = fail

process.on('unhandledRejection', (err) => {
  fail(err)
})
