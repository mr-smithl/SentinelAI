export const STATUS_COLORS = {
  NORMAL: { fill: '#10B981', ring: '#059669', label: 'Normal' },
  SUSPICIOUS: { fill: '#F59E0B', ring: '#D97706', label: 'Suspicious' },
  ALERT: { fill: '#EF4444', ring: '#DC2626', label: 'Alert' },
  'HIGH RISK': { fill: '#DC2626', ring: '#991B1B', label: 'High Risk' },
  CRITICAL: { fill: '#7F1D1D', ring: '#450A0A', label: 'Critical' },
  MAINTENANCE: { fill: '#8B5CF6', ring: '#6D28D9', label: 'Maintenance' },
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
