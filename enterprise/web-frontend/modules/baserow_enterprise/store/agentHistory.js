import AgentApplicationService from '@baserow_enterprise/services/agentApplication'
import { chatMatchesOrigin } from '@baserow_enterprise/utils/agentChatOrigin'

const PAGE_SIZE = 50

function sortChats(chats) {
  chats.sort(
    (a, b) =>
      Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)) ||
      new Date(b.updated_on).getTime() - new Date(a.updated_on).getTime()
  )
}

export const state = () => ({
  chats: [],
  loading: false,
  // Pagination of the fetched pages; realtime upserts can grow `chats`
  // independently, so the fetched offset is tracked separately.
  fetchedCount: 0,
  hasMore: false,
  // Only conversations started this way are listed (see `getChatOrigin`);
  // null lists all of them.
  origin: null,
  // The agent the list belongs to; another agent starts unfiltered.
  applicationId: null,
})

export const mutations = {
  SET_CHATS(state, chats) {
    sortChats(chats)
    state.chats = chats
  },
  APPEND_CHATS(state, chats) {
    for (const chat of chats) {
      const index = state.chats.findIndex((c) => c.id === chat.id)
      if (index !== -1) {
        state.chats.splice(index, 1, { ...state.chats[index], ...chat })
      } else {
        state.chats.push(chat)
      }
    }
    sortChats(state.chats)
  },
  UPSERT_CHAT(state, chat) {
    const index = state.chats.findIndex((c) => c.id === chat.id)
    if (index !== -1) {
      state.chats.splice(index, 1, { ...state.chats[index], ...chat })
    } else {
      state.chats.push(chat)
    }
    sortChats(state.chats)
  },
  REMOVE_CHAT(state, chatId) {
    const index = state.chats.findIndex((chat) => chat.id === chatId)
    if (index !== -1) {
      state.chats.splice(index, 1)
    }
  },
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_ORIGIN(state, origin) {
    state.origin = origin
  },
  SET_APPLICATION_ID(state, applicationId) {
    state.applicationId = applicationId
  },
  SET_PAGINATION(state, { fetchedCount, hasMore }) {
    state.fetchedCount = fetchedCount
    state.hasMore = hasMore
  },
}

export const actions = {
  clear({ commit }) {
    commit('SET_CHATS', [])
    commit('SET_PAGINATION', { fetchedCount: 0, hasMore: false })
    commit('SET_ORIGIN', null)
    commit('SET_APPLICATION_ID', null)
  },
  async fetch({ commit, state }, { applicationId }) {
    if (state.applicationId !== applicationId) {
      commit('SET_APPLICATION_ID', applicationId)
      commit('SET_ORIGIN', null)
    }
    commit('SET_LOADING', true)
    const origin = state.origin
    try {
      const { data } = await AgentApplicationService(this.$client).getChats(
        applicationId,
        { limit: PAGE_SIZE, offset: 0, origin }
      )
      // Another filter was picked while this page loaded.
      if (state.origin !== origin) {
        return state.chats
      }
      commit('SET_CHATS', data.results)
      commit('SET_PAGINATION', {
        fetchedCount: data.results.length,
        hasMore: data.next !== null,
      })
      return data.results
    } finally {
      commit('SET_LOADING', false)
    }
  },
  async fetchMore({ commit, state }, { applicationId }) {
    if (!state.hasMore || state.loading) {
      return
    }
    commit('SET_LOADING', true)
    try {
      const { data } = await AgentApplicationService(this.$client).getChats(
        applicationId,
        { limit: PAGE_SIZE, offset: state.fetchedCount, origin: state.origin }
      )
      commit('APPEND_CHATS', data.results)
      commit('SET_PAGINATION', {
        fetchedCount: state.fetchedCount + data.results.length,
        hasMore: data.next !== null,
      })
      return data.results
    } finally {
      commit('SET_LOADING', false)
    }
  },
  async setOrigin({ commit, dispatch, state }, { applicationId, origin }) {
    const previous = state.origin
    commit('SET_APPLICATION_ID', applicationId)
    commit('SET_ORIGIN', origin)
    try {
      return await dispatch('fetch', { applicationId })
    } catch (error) {
      commit('SET_ORIGIN', previous)
      throw error
    }
  },
  forceUpdateChat({ commit, state, rootGetters }, { chat }) {
    // A filtered list only takes in new conversations that match it.
    const known = state.chats.some((c) => c.id === chat.id)
    if (
      !known &&
      !chatMatchesOrigin(chat, state.origin, rootGetters['auth/getUserId'])
    ) {
      return
    }
    commit('UPSERT_CHAT', chat)
  },
  forceDeleteChat({ commit }, { chatId }) {
    commit('REMOVE_CHAT', chatId)
  },
  async updateChat({ commit, state }, { chatUuid, values }) {
    const chat = state.chats.find((c) => c.uuid === chatUuid)
    const oldValues =
      chat &&
      Object.keys(values).reduce((result, key) => {
        result[key] = chat[key]
        return result
      }, {})
    if (chat) {
      commit('UPSERT_CHAT', { id: chat.id, ...values })
    }
    try {
      const { data } = await AgentApplicationService(this.$client).updateChat(
        chatUuid,
        values
      )
      commit('UPSERT_CHAT', data)
      return data
    } catch (error) {
      if (chat) {
        commit('UPSERT_CHAT', { id: chat.id, ...oldValues })
      }
      throw error
    }
  },
  async deleteChat({ commit, dispatch }, { chat }) {
    await AgentApplicationService(this.$client).deleteChat(chat.uuid)
    commit('REMOVE_CHAT', chat.id)
    dispatch('agentChat/handleChatDeleted', { chatId: chat.id }, { root: true })
  },
}

export const getters = {
  getChats: (state) => state.chats,
  getPinnedChats: (state) => state.chats.filter((chat) => chat.pinned),
  getRecentChats: (state) => state.chats.filter((chat) => !chat.pinned),
  isLoading: (state) => state.loading,
  hasMore: (state) => state.hasMore,
  getOrigin: (state) => state.origin,
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
