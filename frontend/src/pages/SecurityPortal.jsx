import { useState } from 'react'
import { Link } from 'react-router-dom'
import InfrastructureMap from '../components/InfrastructureMap'
import AIInsights from '../components/AIInsights'
import { useSentinel } from '../hooks/useSentinel'
import { STATUS_COLORS, statusBadge, riskText } from '../utils/status'

export default function SecurityPortal() {
  const { stations, alerts, notifications, liveEvent, connected, simulate, toasts } = useSentinel('security')
  const [selected, setSelected] = useState(null)

  const activeThreats = stations.filter((s) => s.status && !['NORMAL', 'MAINTENANCE'].includes(s.status))

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-red-900/30 bg-slate-900/90 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-slate-500 hover:text-slate-300 text-sm">← Portals</Link>
          <div>
            <h1 className="text-lg font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              Security Operations Center
            </h1>
            <p className="text-xs text-slate-500">Intrusion detection · Dispatch · Incident response</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded-full border ${connected ? 'border-emerald-500/50 text-emerald-400' : 'border-slate-600 text-slate-500'}`}>
            {connected ? '● Live feed' : '○ Offline'}
          </span>
          {activeThreats.length > 0 && (
            <span className="text-xs px-3 py-1 rounded-lg bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">
              {activeThreats.length} site(s) under threat
            </span>
          )}
        </div>
      </header>

      <main className="p-6 max-w-[1700px] mx-auto grid grid-cols-1 xl:grid-cols-3 gap-6">
        <section className="xl:col-span-2 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Gauteng Infrastructure — Live Status Map</h2>
            <div className="flex flex-wrap gap-2 text-xs">
              {Object.entries(STATUS_COLORS).map(([k, v]) => (
                <span key={k} className="flex items-center gap-1 text-slate-400">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: v.fill }} />
                  {v.label}
                </span>
              ))}
            </div>
          </div>
          <InfrastructureMap stations={stations} onSelect={setSelected} />
        </section>

        <section className="space-y-4">
          <AIInsights ai={liveEvent?.ai} />

          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Dispatch Notifications</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {notifications.length === 0 && (
                <p className="text-sm text-slate-500">No dispatch notifications yet</p>
              )}
              {notifications.map((n) => (
                <div key={n.id} className="rounded-lg bg-red-950/30 border border-red-500/20 p-3">
                  <p className="text-sm font-medium text-red-200">{n.title}</p>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">{n.body}</p>
                  <p className="text-xs text-slate-600 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
          </div>

          {toasts.length > 0 && (
            <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
              <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Live notifications</h3>
              <div className="space-y-2 max-h-44 overflow-y-auto">
                {toasts.map((t) => (
                  <div key={t.id} className="rounded-lg bg-slate-950/80 border border-slate-700 p-3">
                    <p className="text-sm font-semibold text-slate-100">{t.title}</p>
                    <p className="text-xs text-slate-400 mt-1">{t.message}</p>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-slate-600 mt-1">{t.timestamp}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Simulate intrusion (demo)</h3>
            <div className="grid grid-cols-2 gap-2">
              <DemoBtn onClick={() => simulate('door_open', selected?.id)}>
                Door forced
              </DemoBtn>
              <DemoBtn onClick={() => simulate('motion_detected', selected?.id)}>
                Motion PIR
              </DemoBtn>
              <DemoBtn onClick={() => simulate('light_intrusion', selected?.id)}>
                Torch / light
              </DemoBtn>
              <DemoBtn onClick={() => simulate('flame_ir', selected?.id)}>
                IR spike
              </DemoBtn>
            </div>
          </div>

          {selected && (
            <div className="rounded-xl bg-slate-900 border border-slate-700 p-4">
              <p className="font-medium">{selected.name}</p>
              <p className="text-xs text-slate-500">{selected.owner}</p>
              <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded border ${statusBadge[selected.status]}`}>{selected.status}</span>
            </div>
          )}
        </section>

        <section className="xl:col-span-3 rounded-xl bg-slate-900 border border-slate-800 p-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">Security Incident Log</h2>
          <AlertTable alerts={alerts} />
        </section>
      </main>
    </div>
  )
}

function AlertTable({ alerts }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-xs text-slate-500 uppercase border-b border-slate-800">
          <tr>
            <th className="py-2 pr-4 text-left">Time</th>
            <th className="py-2 pr-4 text-left">Site</th>
            <th className="py-2 pr-4 text-left">Event</th>
            <th className="py-2 pr-4 text-left">Risk</th>
            <th className="py-2 pr-4 text-left">AI Intrusion</th>
            <th className="py-2 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          {alerts.length === 0 && (
            <tr><td colSpan={6} className="py-8 text-center text-slate-500">No security incidents recorded</td></tr>
          )}
          {alerts.map((a) => (
            <tr key={a.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
              <td className="py-3 pr-4 text-slate-400 whitespace-nowrap">{new Date(a.created_at).toLocaleString()}</td>
              <td className="py-3 pr-4">{a.site_id?.replace(/-/g, ' ') || a.asset_id}</td>
              <td className="py-3 pr-4 capitalize">{a.event?.replace(/_/g, ' ')}</td>
              <td className={`py-3 pr-4 font-semibold ${riskText[a.risk_level]}`}>{a.risk_score}%</td>
              <td className="py-3 pr-4 text-indigo-300">{a.intrusion_probability != null ? `${a.intrusion_probability}%` : '—'}</td>
              <td className="py-3">
                <span className={`text-xs px-2 py-0.5 rounded border ${statusBadge[a.status]}`}>{a.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function DemoBtn({ children, onClick }) {
  return (
    <button onClick={onClick} className="py-2 px-3 rounded-lg bg-slate-800 border border-slate-600 text-slate-200 text-sm hover:bg-red-950/40 hover:border-red-500/40 transition">
      {children}
    </button>
  )
}
