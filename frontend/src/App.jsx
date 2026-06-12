import { useCallback, useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import L from 'leaflet'

const API = import.meta.env.DEV ? '' : ''
const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`

const statusColor = {
  NORMAL: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  SUSPICIOUS: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  ALERT: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  'HIGH RISK': 'bg-red-500/20 text-red-300 border-red-500/40',
  MAINTENANCE: 'bg-violet-500/20 text-violet-300 border-violet-500/40',
  CRITICAL: 'bg-red-600/30 text-red-200 border-red-500/50',
}

function riskBadge(level) {
  const map = {
    LOW: 'text-emerald-400',
    MODERATE: 'text-amber-400',
    HIGH: 'text-orange-400',
    CRITICAL: 'text-red-400',
    MAINTENANCE: 'text-violet-400',
  }
  return map[level] || 'text-slate-400'
}

const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

export default function App() {
  const [assets, setAssets] = useState([])
  const [alerts, setAlerts] = useState([])
  const [liveEvent, setLiveEvent] = useState(null)
  const [maintenance, setMaintenance] = useState(false)
  const [connected, setConnected] = useState(false)

  const fetchData = useCallback(async () => {
    const [a, b] = await Promise.all([
      fetch(`${API}/api/assets`).then((r) => r.json()),
      fetch(`${API}/api/alerts?limit=30`).then((r) => r.json()),
    ])
    setAssets(a)
    setAlerts(b)
  }, [])

  useEffect(() => {
    fetchData()
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (msg) => {
      const packet = JSON.parse(msg.data)
      if (packet.type === 'sensor_event' || packet.type === 'maintenance') {
        setLiveEvent(packet.data)
        fetchData()
      }
    }
    return () => ws.close()
  }, [fetchData])

  const systemStatus = useMemo(() => {
    if (maintenance) return 'MAINTENANCE'
    const top = liveEvent?.status || alerts[0]?.status || assets[0]?.status || 'NORMAL'
    return top
  }, [maintenance, liveEvent, alerts, assets])

  const primaryAsset = assets[0]
  const telemetry = primaryAsset?.telemetry

  async function simulate(scenario) {
    await fetch(`${API}/api/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario }),
    })
  }

  async function toggleMaintenance() {
    const next = !maintenance
    await fetch(`${API}/api/maintenance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: next }),
    })
    setMaintenance(next)
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">SentinelAI</h1>
          <p className="text-sm text-slate-400">Predict · Protect · Prevent — Infrastructure Theft Detection</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded-full border ${connected ? 'border-emerald-500/50 text-emerald-400' : 'border-slate-600 text-slate-500'}`}>
            {connected ? '● Live' : '○ Offline'}
          </span>
          <span className={`text-sm font-medium px-3 py-1.5 rounded-lg border ${statusColor[systemStatus] || statusColor.NORMAL}`}>
            {systemStatus}
          </span>
        </div>
      </header>

      <main className="p-6 grid grid-cols-1 xl:grid-cols-3 gap-6 max-w-[1600px] mx-auto">
        {/* Map */}
        <section className="xl:col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">Gauteng Infrastructure Map</h2>
          <div className="h-[420px] rounded-lg overflow-hidden">
            <MapContainer center={[-26.18, 28.02]} zoom={13} className="h-full w-full" scrollWheelZoom>
              <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution="&copy; OpenStreetMap" />
              {assets.map((asset) => (
                <Marker key={asset.id} position={[asset.lat, asset.lon]} icon={markerIcon}>
                  <Popup>
                    <strong>{asset.name}</strong>
                    <br />
                    Status: {asset.status}
                    <br />
                    Type: {asset.asset_type}
                  </Popup>
                  {asset.status !== 'NORMAL' && (
                    <Circle center={[asset.lat, asset.lon]} radius={400} pathOptions={{ color: '#E24B4A', fillOpacity: 0.15 }} />
                  )}
                </Marker>
              ))}
            </MapContainer>
          </div>
        </section>

        {/* Live sensors */}
        <section className="bg-slate-900 rounded-xl border border-slate-800 p-4 space-y-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Live Sensor Node</h2>
          <p className="text-xs text-slate-500">TRANSFORMER-001 — Arduino Uno</p>

          <div className="grid grid-cols-2 gap-3">
            <SensorCard label="Temperature" value={telemetry?.temp_c != null ? `${Number(telemetry.temp_c).toFixed(1)}°C` : '—'} warn={telemetry?.temp_c >= 65} critical={telemetry?.temp_c >= 80} />
            <SensorCard label="Light Level" value={telemetry?.light_level ?? '—'} warn={telemetry?.light_level > 400} />
            <SensorCard label="Door" value={telemetry?.door_open ? 'OPEN' : 'Closed'} warn={!!telemetry?.door_open} />
            <SensorCard label="IR/Flame" value={telemetry?.flame_detected ? 'Detected' : 'Clear'} warn={!!telemetry?.flame_detected} />
          </div>

          {liveEvent && (
            <div className="rounded-lg bg-slate-800/80 p-3 border border-slate-700">
              <p className="text-xs text-slate-400">Latest event</p>
              <p className="font-medium capitalize">{liveEvent.event?.replace(/_/g, ' ')}</p>
              <p className={`text-2xl font-bold ${riskBadge(liveEvent.risk_level)}`}>{liveEvent.risk_score}%</p>
              <p className="text-sm text-slate-400">{liveEvent.message}</p>
            </div>
          )}

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Demo controls (no Arduino needed)</p>
            <div className="grid grid-cols-2 gap-2">
              <DemoBtn onClick={() => simulate('door_open')}>Door opened</DemoBtn>
              <DemoBtn onClick={() => simulate('light_intrusion')}>Torch / light</DemoBtn>
              <DemoBtn onClick={() => simulate('overheat')}>Overheat</DemoBtn>
              <DemoBtn onClick={() => simulate('flame_ir')}>IR / flame</DemoBtn>
            </div>
            <button
              onClick={toggleMaintenance}
              className={`w-full mt-2 py-2 rounded-lg text-sm font-medium border transition ${maintenance ? 'bg-violet-600/30 border-violet-500 text-violet-200' : 'bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700'}`}
            >
              {maintenance ? 'Exit maintenance mode' : 'Enable maintenance mode'}
            </button>
          </div>
        </section>

        {/* Alert log */}
        <section className="xl:col-span-3 bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">Alert Log & Incident Tracking</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase border-b border-slate-800">
                <tr>
                  <th className="py-2 pr-4">Time</th>
                  <th className="py-2 pr-4">Asset</th>
                  <th className="py-2 pr-4">Event</th>
                  <th className="py-2 pr-4">Risk</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2">Message</th>
                </tr>
              </thead>
              <tbody>
                {alerts.length === 0 && (
                  <tr><td colSpan={6} className="py-8 text-center text-slate-500">No alerts yet — trigger a sensor or use demo buttons</td></tr>
                )}
                {alerts.map((a) => (
                  <tr key={a.id} className="border-b border-slate-800/60 hover:bg-slate-800/40">
                    <td className="py-3 pr-4 text-slate-400 whitespace-nowrap">{new Date(a.created_at).toLocaleString()}</td>
                    <td className="py-3 pr-4">{a.asset_id}</td>
                    <td className="py-3 pr-4 capitalize">{a.event?.replace(/_/g, ' ')}</td>
                    <td className={`py-3 pr-4 font-semibold ${riskBadge(a.risk_level)}`}>{a.risk_score}%</td>
                    <td className="py-3 pr-4">
                      <span className={`text-xs px-2 py-0.5 rounded border ${statusColor[a.status] || ''}`}>{a.status}</span>
                    </td>
                    <td className="py-3 text-slate-400">{a.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}

function SensorCard({ label, value, warn, critical }) {
  const border = critical ? 'border-red-500/60' : warn ? 'border-amber-500/50' : 'border-slate-700'
  const text = critical ? 'text-red-300' : warn ? 'text-amber-300' : 'text-slate-100'
  return (
    <div className={`rounded-lg bg-slate-800/60 border p-3 ${border}`}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-lg font-semibold ${text}`}>{value}</p>
    </div>
  )
}

function DemoBtn({ children, onClick }) {
  return (
    <button onClick={onClick} className="py-2 px-3 rounded-lg bg-slate-800 border border-slate-600 text-slate-200 text-sm hover:bg-slate-700 transition">
      {children}
    </button>
  )
}
