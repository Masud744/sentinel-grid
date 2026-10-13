import React from 'react';
import { ShieldAlert, ArrowUpRight, Users, Clock, Flame } from 'lucide-react';

export interface PriorityItem {
  rank: number;
  zone_id: string;
  zone_name: string;
  risk_score: number;
  state: string;
  occupancy_factor: number;
  duration_critical_seconds: number;
  reason: string;
}

interface PriorityQueueProps {
  items: PriorityItem[];
}

export const PriorityQueue: React.FC<PriorityQueueProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <div className="glass-panel p-6 text-center border-dashed border-slate-800">
        <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-3">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h4 className="font-semibold text-slate-200 mb-1">Campus Grid Idle</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          All campus zones are currently SAFE. No critical incidents requiring response priority ranking.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel p-5 border-rose-500/30">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400">
            <Flame className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base tracking-wide flex items-center gap-2">
              Multi-Zone Response Priority Queue
              <span className="text-xs bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded-full font-semibold border border-rose-500/30">
                {items.length} Active CRITICAL
              </span>
            </h3>
            <p className="text-xs text-slate-400">Server-side multi-tier emergency ranking (Risk Score &gt; Occupancy &gt; Duration)</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.zone_id}
            className="bg-slate-900/90 border border-rose-500/40 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-rose-500/70 transition-all"
          >
            <div className="flex items-center space-x-3">
              {/* Rank Badge */}
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-600 to-red-700 text-white font-extrabold text-lg flex items-center justify-center shadow-lg shadow-rose-950/50 shrink-0">
                #{item.rank}
              </div>

              <div>
                <h4 className="font-bold text-white text-base flex items-center gap-2">
                  {item.zone_name}
                  {item.occupancy_factor >= 1.0 && (
                    <span className="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                      <Users className="w-3 h-3" /> OCCUPIED LAB
                    </span>
                  )}
                </h4>
                <p className="text-xs text-rose-300/90 font-medium mt-0.5 flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5 text-rose-400" />
                  {item.reason}
                </p>
              </div>
            </div>

            {/* Score & Duration */}
            <div className="flex items-center space-x-4 border-t sm:border-t-0 sm:border-l border-slate-800 pt-2 sm:pt-0 sm:pl-4">
              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Risk Score</span>
                <span className="text-xl font-extrabold text-rose-400">{item.risk_score.toFixed(1)}</span>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Active For</span>
                <span className="text-sm font-bold text-slate-200 flex items-center justify-end gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {item.duration_critical_seconds.toFixed(0)}s
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
