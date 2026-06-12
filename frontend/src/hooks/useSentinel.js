import { useCallback, useEffect, useState } from 'react'

const API = import.meta.env.DEV ? '' : ''
const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`

export function useSentinel(audience) {
  const [stations, setStations] = useState([])
  const [alerts, setAlerts] = useState([])
  const [notifications, setNotifications] = useState([])
  const [liveEvent, setLiveEvent] = useState(null)
  const [toasts, setToasts] = useState([])
  const [connected, setConnected] = useState(false)

  const fetchAll = useCallback(async () => {
    const q = audience ? `?audience=${audience}&limit=40` : '?limit=40'
    const [s, a, n] = await Promise.all([
      fetch(`${API}/api/stations`).then((r) => r.json()),
      fetch(`${API}/api/alerts${q}`).then((r) => r.json()),
      audience
        ? fetch(`${API}/api/notifications/${audience}?limit=15`).then((r) => r.json())
        : Promise.resolve([]),
    ])
    setStations(s)
    setAlerts(a)
    setNotifications(n)
  }, [audience])

  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().catch(() => {})
    }

    fetchAll()
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (msg) => {
      const packet = JSON.parse(msg.data)
      if (packet.type === 'sensor_event' || packet.type === 'maintenance') {
        const eventData = packet.data
        setLiveEvent(eventData)
        const title = `${eventData.status || 'Alert'} — ${eventData.event?.replace(/_/g, ' ')}`
        const message = `${eventData.site_id?.replace(/-/g, ' ') || eventData.asset_id}`
        setToasts((current) => [
          { id: Date.now(), title, message, timestamp: new Date().toLocaleTimeString() },
          ...current,
        ].slice(0, 5))
        if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
          new Notification(title, { body: message })
        }
        fetchAll()
      }
    }
    return () => ws.close()
  }, [fetchAll])

  async function simulate(scenario, site_id = null) {
    await fetch(`${API}/api/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, site_id }),
    })
  }

  async function toggleMaintenance(enabled, site_id = null) {
    await fetch(`${API}/api/maintenance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled, site_id }),
    })
  }

  return {
    stations,
    alerts,
    notifications,
    liveEvent,
    toasts,
    connected,
    simulate,
    toggleMaintenance,
    refresh: fetchAll,
  }
}
