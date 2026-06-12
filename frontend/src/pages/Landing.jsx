import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="text-center max-w-2xl mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium mb-6">
            Gauteng G13 Hackathon · Infrastructure Protection
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            Sentinel<span className="text-emerald-400">AI</span>
          </h1>
          <p className="text-lg text-slate-400 leading-relaxed">
            Predict. Protect. Prevent. AI-powered monitoring for power stations and substations
            across Gauteng — with dedicated portals for security response and utility operations.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 w-full max-w-3xl">
          <Link
            to="/security"
            className="group rounded-2xl border border-slate-700 bg-slate-900/80 p-8 hover:border-red-500/50 hover:bg-slate-900 transition shadow-lg"
          >
            <div className="w-12 h-12 rounded-xl bg-red-500/15 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition">🛡️</div>
            <h2 className="text-xl font-semibold text-white mb-2">Security Company Portal</h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Real-time intrusion alerts, AI break-in probability, dispatch notifications,
              and incident tracking for private security and rapid response teams.
            </p>
            <p className="text-xs text-red-400 mt-4 font-medium">Door · Motion · Light · Tamper alerts →</p>
          </Link>

          <Link
            to="/operations"
            className="group rounded-2xl border border-slate-700 bg-slate-900/80 p-8 hover:border-violet-500/50 hover:bg-slate-900 transition shadow-lg"
          >
            <div className="w-12 h-12 rounded-xl bg-violet-500/15 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition">⚡</div>
            <h2 className="text-xl font-semibold text-white mb-2">Utility Operations Portal</h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Asset health monitoring, transformer temperature, maintenance mode scheduling,
              and operational notices for municipal and Eskom maintenance teams.
            </p>
            <p className="text-xs text-violet-400 mt-4 font-medium">Thermal · Maintenance · Asset health →</p>
          </Link>
        </div>
      </div>

      <footer className="text-center text-xs text-slate-600 py-6 border-t border-slate-800">
        SentinelAI · Intelligent Infrastructure Protection System
      </footer>
    </div>
  )
}
