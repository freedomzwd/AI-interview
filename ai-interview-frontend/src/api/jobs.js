import api from './request'

export function getJobs(params) {
  return api.get('/jobs', { params })
}
