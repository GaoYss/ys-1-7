import { http } from './http'

export const quotesApi = {
  list(params = {}) {
    return http.get('/quotes', { params })
  },
  create(payload) {
    return http.post('/quotes', payload)
  },
  update(id, payload) {
    return http.put(`/quotes/${id}`, payload)
  },
  remove(id) {
    return http.delete(`/quotes/${id}`)
  },
  recommend(params = {}) {
    return http.get('/quotes/recommend', { params })
  },
  options() {
    return http.get('/quotes/options')
  }
}
