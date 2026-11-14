import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, color = 'indigo', badge }) {
  const colorMap = {
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    sky: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  };

  const badgeColorMap = {
    green: 'bg-emerald-950 text-emerald-300 border-emerald-800',
    red: 'bg-rose-950 text-rose-300 border-rose-800',
    amber: 'bg-amber-950 text-amber-300 border-amber-800',
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {title}
        </span>
        {Icon && (
          <div className={`p-2 rounded-lg border ${colorMap[color]}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div className="text-2xl sm:text-3xl font-bold text-slate-100 font-mono">
          {value !== undefined && value !== null ? value : '--'}
        </div>
        {badge && (
          <span
            className={`text-xs px-2 py-0.5 rounded-full border font-mono ${
              badgeColorMap[badge.type] || 'bg-slate-800 text-slate-300'
            }`}
          >
            {badge.text}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-400 truncate">
          {subtitle}
        </p>
      )}
    </div>
  );
}
