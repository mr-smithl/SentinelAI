import L from 'leaflet'
import { STATUS_COLORS } from './status'

const ICON_PATHS = {
  power_station: 'M12 2L4 7v10l8 5 8-5V7L12 2zm0 2.2l5.5 3.4v6.8L12 18.8 6.5 14.4V7.6L12 4.2z M11 9h2v6h-2z',
  substation: 'M4 10h16v2H4zm2-4h12l-2 4H8L6 6zm-2 8h16v2H4z',
  monitored: 'M12 2a7 7 0 00-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 00-7-7zm0 9.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z',
}

function svgIcon(path, color, ring, size = 36) {
  const html = `
    <div style="position:relative;width:${size}px;height:${size}px;">
      <div style="position:absolute;inset:-4px;border-radius:50%;background:${ring}33;border:2px solid ${ring};animation:${color !== '#1D9E75' ? 'pulse 2s infinite' : 'none'}"></div>
      <svg viewBox="0 0 24 24" width="${size}" height="${size}" style="position:relative;z-index:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,.45))">
        <circle cx="12" cy="12" r="11" fill="${color}" stroke="${ring}" stroke-width="1.5"/>
        <path d="${path}" fill="white" transform="scale(0.55) translate(10,10)"/>
      </svg>
    </div>`
  return L.divIcon({
    html,
    className: 'sentinel-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  })
}

export function stationIcon(site) {
  const colors = STATUS_COLORS[site.status] || STATUS_COLORS.NORMAL
  const path = site.has_sensors
    ? ICON_PATHS.monitored
    : site.category === 'power_station'
      ? ICON_PATHS.power_station
      : ICON_PATHS.substation
  return svgIcon(path, colors.fill, colors.ring, site.has_sensors ? 40 : 32)
}
