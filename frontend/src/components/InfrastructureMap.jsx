import { MapContainer, TileLayer, Marker, Popup, Circle, LayersControl, ScaleControl } from 'react-leaflet'
import { stationIcon } from '../utils/mapIcons'
import { STATUS_COLORS, statusBadge } from '../utils/status'

export default function InfrastructureMap({ stations, height = '520px', onSelect }) {
  const alertSites = stations.filter((s) => s.status && s.status !== 'NORMAL')

  return (
    <div className="rounded-xl overflow-hidden border border-slate-700/80 shadow-xl" style={{ height }}>
      <MapContainer
        center={[-26.12, 28.08]}
        zoom={9}
        className="h-full w-full"
        scrollWheelZoom
        zoomControl
      >
        <ScaleControl position="bottomleft" />
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="Dark Street">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              maxZoom={19}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite">
            <TileLayer
              attribution="Tiles &copy; Esri"
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              maxZoom={19}
            />
          </LayersControl.BaseLayer>
          <LayersControl.Overlay name="Terrain labels">
            <TileLayer
              url="https://stamen-tiles.a.ssl.fastly.net/terrain-labels/{z}/{x}/{y}.png"
              opacity={0.6}
            />
          </LayersControl.Overlay>
        </LayersControl>

        {alertSites.map((site) => (
          <Circle
            key={`ring-${site.id}`}
            center={[site.lat, site.lon]}
            radius={site.has_sensors ? 1200 : 800}
            pathOptions={{
              color: (STATUS_COLORS[site.status] || STATUS_COLORS.ALERT).ring,
              fillColor: (STATUS_COLORS[site.status] || STATUS_COLORS.ALERT).fill,
              fillOpacity: 0.12,
              weight: 2,
              dashArray: site.status === 'MAINTENANCE' ? '6 4' : undefined,
            }}
          />
        ))}

        {stations.map((site) => (
          <Marker
            key={site.id}
            position={[site.lat, site.lon]}
            icon={stationIcon(site)}
            eventHandlers={{ click: () => onSelect?.(site) }}
          >
            <Popup>
              <div className="text-slate-800 min-w-[200px]">
                <p className="font-semibold text-base">{site.name}</p>
                <p className="text-xs text-slate-500">{site.facility_type}</p>
                <p className="text-xs text-slate-500">{site.owner}</p>
                <p className="mt-2">
                  <span className={`text-xs px-2 py-0.5 rounded border ${statusBadge[site.status] || statusBadge.NORMAL}`}>
                    {site.status}
                  </span>
                  {site.risk_score > 0 && (
                    <span className="ml-2 text-xs font-bold text-red-600">{site.risk_score}% risk</span>
                  )}
                </p>
                {site.has_sensors && (
                  <p className="text-xs mt-1 text-emerald-700 font-medium">● Live sensor node</p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
