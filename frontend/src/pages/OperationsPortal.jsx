import { useState } from 'react'
import { Link } from 'react-router-dom'
import InfrastructureMap from '../components/InfrastructureMap'
import AIInsights from '../components/AIInsights'
import { useSentinel } from '../hooks/useSentinel'
import { statusBadge, riskText } from '../utils/status'

export default function OperationsPortal() {
  const { stations, alerts, notifications, liveEvent, connected, simulate, toggleMaintenance, toasts } = useSentinel('operations')
  const [maintenance, setMaintenance] = useState(false)
  const [selected, setSelected] = useState(null)

  const monitored = stations.find((s) => s.has_sensors)
  const tel = monitored?.telemetry

  async function handleMaintenance() {
    const next = !maintenance
    await toggleMaintenance(next, selected?.id || monitored?.id)
    setMaintenance(next)
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-violet-900/30 bg-slate-900/90 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-slate-500 hover:text-slate-300 text-sm">← Portals</Link>
          <div>
            <h1 className="text-lg font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-violet-500" />
              Utility Operations & Maintenance
            </h1>
            <p className="text-xs text-slate-500">Asset health · Thermal monitoring · Maintenance scheduling</p>
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full border ${connected ? 'border-emerald-500/50 text-emerald-400' : 'border-slate-600 text-slate-500'}`}>
          {connected ? '● Live feed' : '○ Offline'}
        </span>
      </header>

      <main className="p-6 max-w-[1700px] mx-auto grid grid-cols-1 xl:grid-cols-3 gap-6">
        <section className="xl:col-span-2">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">Infrastructure Network — Operational View</h2>
          <InfrastructureMap stations={stations} height="480px" onSelect={setSelected} />
        </section>

        <section className="space-y-4">
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-1">Monitored Node</h3>
            <p className="font-medium text-white">{selected?.name || monitored?.name || 'John Ware Substation'}</p>
            <p className="text-xs text-slate-500 mb-4">
              {selected ? 'Selected site from the map' : 'Live Arduino sensor cluster'}
            </p>

            <div className="grid grid-cols-2 gap-3">
              <SensorCard label="Surface Temp" value={tel?.temp_c != null ? `${Number(tel.temp_c).toFixed(1)}°C` : '—'} warn={tel?.temp_c >= 65} critical={tel?.temp_c >= 80} />
              <SensorCard label="Light (LDR)" value={tel?.light_level ?? '—'} warn={tel?.light_level > 400} />
              <SensorCard label="Door / Tamper" value={tel?.door_open ? 'OPEN' : 'Secure'} warn={!!tel?.door_open} />
              <SensorCard label="Motion (PIR)" value={tel?.motion_detected ? 'Detected' : 'Clear'} warn={!!tel?.motion_detected} />
              <SensorCard label="IR / Flame" value={tel?.flame_detected ? 'Active' : 'Clear'} warn={!!tel?.flame_detected} />
              <SensorCard label="Maintenance" value={tel?.maintenance_mode ? 'ON' : 'Off'} warn={!!tel?.maintenance_mode} />
            </div>
          </div>

          <AIInsights ai={liveEvent?.ai} compact={false} />

          <button
            onClick={handleMaintenance}
            className={`w-full py-3 rounded-xl text-sm font-medium border transition ${
              maintenance
                ? 'bg-violet-600/30 border-violet-500 text-violet-200'
                : 'bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {maintenance ? 'Exit maintenance mode' : 'Enable maintenance mode'}
          </button>

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
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Operations notices</h3>
            {notifications.length === 0 ? (
              <p className="text-sm text-slate-500">No operational notices</p>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="rounded-lg bg-violet-950/20 border border-violet-500/20 p-3 mb-2">
                  <p className="text-sm text-violet-200">{n.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                </div>
              ))
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <DemoBtn onClick={() => simulate('overheat', selected?.id || monitored?.id)}>
              Simulate overheat
            </DemoBtn>
            <DemoBtn onClick={() => simulate('door_open', selected?.id || monitored?.id)}>
              Simulate tamper
            </DemoBtn>
          </div>
        </section>

        <section className="xl:col-span-3 rounded-xl bg-slate-900 border border-slate-800 p-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">Operations Alert History</h2>
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-500 uppercase border-b border-slate-800">
              <tr>
                <th className="py-2 pr-4 text-left">Time</th>
                <th className="py-2 pr-4 text-left">Site</th>
                <th className="py-2 pr-4 text-left">Event</th>
                <th className="py-2 pr-4 text-left">Temp</th>
                <th className="py-2 pr-4 text-left">AI Assessment</th>
                <th className="py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 && (
                <tr><td colSpan={6} className="py-8 text-center text-slate-500">No operational alerts</td></tr>
              )}
              {alerts.map((a) => (
                <tr key={a.id} className="border-b border-slate-800/50">
                  <td className="py-3 pr-4 text-slate-400">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="py-3 pr-4">{a.site_id?.replace(/-/g, ' ')}</td>
                  <td className="py-3 pr-4 capitalize">{a.event?.replace(/_/g, ' ')}</td>
                  <td className="py-3 pr-4">{a.temp_c != null ? `${a.temp_c}°C` : '—'}</td>
                  <td className={`py-3 pr-4 ${riskText[a.risk_level]}`}>{a.intrusion_probability ?? a.risk_score}%</td>
                  <td className="py-3"><span className={`text-xs px-2 py-0.5 rounded border ${statusBadge[a.status]}`}>{a.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  )
}

function SensorCard({ label, value, warn, critical }) {
  const border = critical ? 'border-red-500/60' : warn ? 'border-amber-500/50' : 'border-slate-700'
  const text = critical ? 'text-red-300' : warn ? 'text-amber-300' : 'text-slate-100'
  return (
    <div className={`rounded-lg bg-slate-800/50 border p-3 ${border}`}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-base font-semibold ${text}`}>{value}</p>
    </div>
  )
}

function DemoBtn({ children, onClick }) {
  return (
    <button onClick={onClick} className="py-2 px-3 rounded-lg bg-slate-800 border border-slate-600 text-sm text-slate-200 hover:bg-violet-950/30 hover:border-violet-500/40 transition">
      {children}
    </button>
  )
}
