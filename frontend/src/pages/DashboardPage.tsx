import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Layout, PageHeader } from '../components/layout/Layout'
import { StatCard, Card } from '../components/ui/Card'
import { StatusBadge } from '../components/ui/StatusBadge'
import { getAllServicesHealth, getSources, getParsers, getPolicies, getConfiguration } from '../api/endpoints'
import type { AllServicesHealth } from '../types'

export function DashboardPage() {
  const { data: health } = useQuery({ queryKey: ['services-health'], queryFn: () => getAllServicesHealth().then(r => r.data), refetchInterval: 30000 })
  const { data: sources } = useQuery({ queryKey: ['sources'], queryFn: () => getSources({ page_size: 1 }).then(r => r.data) })
  const { data: parsers } = useQuery({ queryKey: ['parsers'], queryFn: () => getParsers({ page_size: 1 }).then(r => r.data) })
  const { data: policies } = useQuery({ queryKey: ['policies'], queryFn: () => getPolicies({ page_size: 1 }).then(r => r.data) })
  const { data: config } = useQuery({ queryKey: ['configuration'], queryFn: () => getConfiguration().then(r => r.data) })

  const services = health?.services ?? {}
  const infra = ['postgres', 'redis', 'kafka', 'opensearch', 'minio']
  const modules = ['m1-ingestion', 'm2-parser', 'm3-normalizer', 'm4-enrichment', 'm5-delivery']

  return (
    <Layout>
      <PageHeader title="Dashboard" subtitle="ULPF M6 Control Plane overview" />

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
        <StatCard label="Sources" value={sources?.total ?? '—'} />
        <StatCard label="Parsers" value={parsers?.total ?? '—'} />
        <StatCard label="Policies" value={policies?.total ?? '—'} />
        <StatCard label="Config Version" value={config?.version ?? '—'} color="var(--green)" />
        <StatCard label="M6 Status" value="HEALTHY" color="var(--green)" />
      </div>

      {/* Service health */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <Card title="Infrastructure Health">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {infra.map(svc => {
              const s = services[svc]
              return (
                <div key={svc} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ fontSize: 13 }}>{svc}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {s?.latency_ms != null && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.latency_ms}ms</span>}
                    <StatusBadge status={s?.status ?? 'UNKNOWN'} />
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        <Card title="External Modules (M1–M5)">
          <div style={{ marginBottom: 8, padding: '6px 8px', background: 'var(--bg-elevated)', borderRadius: 4, fontSize: 11, color: 'var(--text-muted)' }}>
            M1–M5 are external services. UNAVAILABLE = not yet connected.
          </div>
          {modules.map(svc => {
            const s = services[svc]
            return (
              <div key={svc} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontSize: 13 }}>{svc}</div>
                  {s?.is_mock && <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>MOCK ADAPTER</div>}
                </div>
                <StatusBadge status={s?.status ?? 'UNKNOWN'} />
              </div>
            )
          })}
        </Card>
      </div>

      {/* Config version */}
      <Card title="Redis Configuration">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 10 }}>
          {['sources', 'parsers', 'schemas', 'mappings', 'policies'].map(key => {
            const val = (config as any)?.[key]
            const count = Array.isArray(val) ? val.length : val ? Object.keys(val).length : 0
            return (
              <div key={key} style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: '10px 12px', textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: count > 0 ? 'var(--green)' : 'var(--text-dim)' }}>{config ? count : '—'}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, textTransform: 'capitalize' }}>{key}</div>
              </div>
            )
          })}
        </div>
        {config?.updated_at && <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-dim)' }}>Last updated: {new Date(config.updated_at).toLocaleString()}</div>}
      </Card>
    </Layout>
  )
}
