import api from './client'
import type { Paginated, Source, Parser, ParserVersion, Schema, Mapping, Policy, AllServicesHealth, AuditLog, ReplayOperation, ConfigSnapshot, TokenResponse, User } from '../types'

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (username: string, password: string) => {
  const form = new FormData()
  form.append('username', username)
  form.append('password', password)
  return api.post<TokenResponse>('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
}
export const getMe = () => api.get<User>('/auth/me')

// ── Sources ───────────────────────────────────────────────────────────────────
export const getSources = (params?: object) => api.get<Paginated<Source>>('/sources', { params })
export const getSource = (id: string) => api.get<Source>(`/sources/${id}`)
export const createSource = (data: object) => api.post<Source>('/sources', data)
export const updateSource = (id: string, data: object) => api.put<Source>(`/sources/${id}`, data)
export const deleteSource = (id: string) => api.delete(`/sources/${id}`)
export const enableSource = (id: string) => api.post<Source>(`/sources/${id}/enable`)
export const disableSource = (id: string) => api.post<Source>(`/sources/${id}/disable`)

// ── Parsers ───────────────────────────────────────────────────────────────────
export const getParsers = (params?: object) => api.get<Paginated<Parser>>('/parsers', { params })
export const getParser = (id: string) => api.get<Parser>(`/parsers/${id}`)
export const createParser = (data: object) => api.post<Parser>('/parsers', data)
export const updateParser = (id: string, data: object) => api.put<Parser>(`/parsers/${id}`, data)
export const submitParser = (id: string, reason?: string) => api.post<Parser>(`/parsers/${id}/submit`, { reason })
export const approveParser = (id: string, reason?: string) => api.post<Parser>(`/parsers/${id}/approve`, { reason })
export const activateParser = (id: string, reason?: string) => api.post<Parser>(`/parsers/${id}/activate`, { reason })
export const disableParser = (id: string, reason?: string) => api.post<Parser>(`/parsers/${id}/disable`, { reason })
export const rollbackParser = (id: string, reason?: string) => api.post<Parser>(`/parsers/${id}/rollback`, { reason })
export const getParserHistory = (id: string) => api.get<ParserVersion[]>(`/parsers/${id}/history`)

// ── Schemas ───────────────────────────────────────────────────────────────────
export const getSchemas = (params?: object) => api.get<Paginated<Schema>>('/schemas', { params })
export const getSchema = (name: string) => api.get<Schema>(`/schemas/${name}`)
export const getSchemaVersion = (name: string, version: string) => api.get(`/schemas/${name}/${version}`)
export const createSchema = (data: object) => api.post<Schema>('/schemas', data)

// ── Mappings ──────────────────────────────────────────────────────────────────
export const getMappings = (params?: object) => api.get<Paginated<Mapping>>('/mappings', { params })
export const getMapping = (id: string) => api.get<Mapping>(`/mappings/${id}`)
export const createMapping = (data: object) => api.post<Mapping>('/mappings', data)
export const updateMapping = (id: string, data: object) => api.put<Mapping>(`/mappings/${id}`, data)

// ── Policies ──────────────────────────────────────────────────────────────────
export const getPolicies = (params?: object) => api.get<Paginated<Policy>>('/policies', { params })
export const getPolicy = (id: string) => api.get<Policy>(`/policies/${id}`)
export const createPolicy = (data: object) => api.post<Policy>('/policies', data)
export const updatePolicy = (id: string, data: object) => api.put<Policy>(`/policies/${id}`, data)
export const enablePolicy = (id: string) => api.post<Policy>(`/policies/${id}/enable`)
export const disablePolicy = (id: string) => api.post<Policy>(`/policies/${id}/disable`)

// ── Services ──────────────────────────────────────────────────────────────────
export const getAllServicesHealth = () => api.get<AllServicesHealth>('/services')
export const getServiceHealth = (service: string) => api.get(`/services/${service}`)

// ── Audit ─────────────────────────────────────────────────────────────────────
export const getAuditLogs = (params?: object) => api.get<Paginated<AuditLog>>('/audit', { params })

// ── Replay ────────────────────────────────────────────────────────────────────
export const requestReplay = (eventId: string, data: object) => api.post<ReplayOperation>(`/replay/${eventId}`, data)
export const getReplays = (params?: object) => api.get<Paginated<ReplayOperation>>('/replay', { params })

// ── Configuration ─────────────────────────────────────────────────────────────
export const getConfiguration = () => api.get<ConfigSnapshot>('/configuration')
export const distributeAll = () => api.post('/configuration/distribute')
export const distributeKey = (key: string) => api.post(`/configuration/distribute/${key}`)
