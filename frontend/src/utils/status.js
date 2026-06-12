export const STATUS_COLORS = {
  NORMAL: { fill: '#1D9E75', ring: '#0F6E56', label: 'Normal' },
  SUSPICIOUS: { fill: '#D4A017', ring: '#BA7517', label: 'Suspicious' },
  ALERT: { fill: '#E67E22', ring: '#CA6F1E', label: 'Alert' },
  'HIGH RISK': { fill: '#E24B4A', ring: '#A32D2D', label: 'High Risk' },
  CRITICAL: { fill: '#C0392B', ring: '#922B21', label: 'Critical' },
  MAINTENANCE: { fill: '#7C6BDB', ring: '#534AB7', label: 'Maintenance' },
}

export const statusBadge = {
  NORMAL: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  SUSPICIOUS: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  ALERT: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  'HIGH RISK': 'bg-red-500/20 text-red-300 border-red-500/40',
  CRITICAL: 'bg-red-600/30 text-red-200 border-red-500/50',
  MAINTENANCE: 'bg-violet-500/20 text-violet-300 border-violet-500/40',
}

export const riskText = {
  LOW: 'text-emerald-400',
  MODERATE: 'text-amber-400',
  HIGH: 'text-orange-400',
  CRITICAL: 'text-red-400',
  MAINTENANCE: 'text-violet-400',
}
