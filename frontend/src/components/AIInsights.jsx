import { riskText } from '../utils/status'

export default function AIInsights({ ai, compact = false }) {
  if (!ai) return null

  if (compact) {
    return (
      <div className="rounded-lg bg-indigo-950/40 border border-indigo-500/30 p-3">
        <p className="text-xs text-indigo-300 uppercase tracking-wider mb-1">AI Intrusion Analysis</p>
        <p className="text-2xl font-bold text-indigo-100">{ai.intrusion_probability}%</p>
        <p className="text-sm text-indigo-200/80">{ai.break_in_likelihood}</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl bg-gradient-to-br from-indigo-950/60 to-slate-900 border border-indigo-500/25 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium text-indigo-300 uppercase tracking-wider">AI Fusion Engine</p>
          <p className="text-sm text-slate-400 mt-0.5">Multi-sensor intrusion probability</p>
        </div>
        <div className="text-right">
          <p className={`text-3xl font-bold ${riskText[ai.threat_class] || 'text-indigo-300'}`}>
            {ai.intrusion_probability}%
          </p>
          <p className="text-xs text-slate-500">confidence {Math.round((ai.confidence || 0) * 100)}%</p>
        </div>
      </div>

      <p className="text-sm font-medium text-indigo-100">{ai.break_in_likelihood}</p>
      <p className="text-sm text-slate-400">{ai.ai_summary}</p>

      {ai.active_signals?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {ai.active_signals.map((s) => (
            <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-200 border border-indigo-500/30">
              {s.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
        {(ai.factors || []).slice(0, 4).map((f, i) => (
          <li key={i}>{f}</li>
        ))}
      </ul>

      <div className="rounded-lg bg-slate-800/60 p-3 border border-slate-700">
        <p className="text-xs text-slate-500 uppercase">Recommended action</p>
        <p className="text-sm text-slate-200 mt-1">{ai.recommended_action}</p>
      </div>
    </div>
  )
}
