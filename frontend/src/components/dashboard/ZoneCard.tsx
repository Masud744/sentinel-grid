import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Flame, Droplets, Wind, Users, Activity, Power, Volume2 } from 'lucide-react';
import { TrendingSparkline } from './TrendingSparkline';

export interface ZoneData {
  id: string;
  name: string;
  lab_type: string;
  is_active: boolean;
  connection_status: 'ONLINE' | 'OFFLINE';
  current_risk_score: number;
  current_state: 'SAFE' | 'WARNING' | 'CRITICAL';
  occupancy_status: 'OCCUPIED' | 'VACANT';
  is_trending_up?: boolean;
  trend_slope?: number;
  last_updated?: string;
}

interface ZoneCardProps {
  zone: ZoneData;
  onAcknowledge?: (zoneId: string) => void;
}

export const ZoneCard: React.FC<ZoneCardProps> = ({ zone }) => {
  const isCritical = zone.current_state === 'CRITICAL';
  const isWarning = zone.current_state === 'WARNING';
  const isSafe = zone.current_state === 'SAFE';

  // Accessibility Color + Icon pairing
  const getStateBadge = () => {
    if (isCritical) {
      return (
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 text-xs font-bold uppercase tracking-wider animate-pulse">
          <AlertOctagon className="w-4 h-4" />
          <span>CRITICAL HAZARD</span>
        </div>
      );
    }
    if (isWarning) {
      return (
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40 text-xs font-bold uppercase tracking-wider">
          <AlertTriangle className="w-4 h-4" />
          <span>ELEVATED WARNING</span>
        </div>
      );
    }
    return (
      <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs font-bold uppercase tracking-wider">
        <ShieldCheck className="w-4 h-4" />
        <span>ZONE SAFE</span>
      </div>
    );
  };

  const getCardBorder = () => {
    if (isCritical) return 'border-rose-500/80 shadow-rose-950/40 pulse-critical';
    if (isWarning) return 'border-amber-500/60 shadow-amber-950/20';
    return 'border-slate-800 hover:border-slate-700';
  };

  return (
    <div className={`glass-panel p-5 relative overflow-hidden transition-all duration-300 ${getCardBorder()}`}>
      
      {/* Top Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="text-lg font-bold text-white tracking-wide">{zone.name}</h3>
            <span className={`w-2 h-2 rounded-full ${zone.connection_status === 'ONLINE' ? 'bg-emerald-400' : 'bg-slate-600'}`} title={zone.connection_status} />
          </div>
          <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">{zone.lab_type.replace('_', ' ')}</p>
        </div>
        {getStateBadge()}
      </div>

      {/* Main Gauge / Risk Score Display */}
      <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800/80 mb-4 flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold block mb-1">Server Computed Risk</span>
          <div className="flex items-baseline space-x-2">
            <span className={`text-3xl font-extrabold tracking-tight ${
              isCritical ? 'text-rose-400' : isWarning ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {zone.current_risk_score.toFixed(1)}
            </span>
            <span className="text-xs text-slate-500 font-medium">/ 100</span>
          </div>
        </div>

        {/* Bonus 2 Isolated Trend Badge */}
        <div className="text-right">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1 font-semibold">Risk Trend (Bonus 2)</span>
          <TrendingSparkline isTrendingUp={zone.is_trending_up} slope={zone.trend_slope} />
        </div>
      </div>

      {/* Sensor Grid Indicators */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          <Flame className={`w-4 h-4 ${isCritical ? 'text-rose-400' : 'text-slate-500'}`} />
          <div>
            <span className="text-[10px] text-slate-400 block">Fire</span>
            <span className="font-semibold text-slate-200">{isCritical ? 'HIGH' : 'SAFE'}</span>
          </div>
        </div>

        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          {zone.lab_type === 'iot_lab' ? (
            <Wind className="w-4 h-4 text-cyan-400" />
          ) : (
            <Droplets className="w-4 h-4 text-blue-400" />
          )}
          <div>
            <span className="text-[10px] text-slate-400 block">{zone.lab_type === 'iot_lab' ? 'Gas' : 'Water'}</span>
            <span className="font-semibold text-slate-200">{isWarning || isCritical ? 'ELEVATED' : 'NORMAL'}</span>
          </div>
        </div>

        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex items-center space-x-2">
          <Users className={`w-4 h-4 ${zone.occupancy_status === 'OCCUPIED' ? 'text-amber-400' : 'text-slate-500'}`} />
          <div>
            <span className="text-[10px] text-slate-400 block">Occupancy</span>
            <span className="font-semibold text-slate-200">{zone.occupancy_status}</span>
          </div>
        </div>
      </div>

      {/* Simulated Actuator Hardware Signals */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <span className="font-medium text-[11px] uppercase tracking-wider text-slate-500">Hardware Actuation:</span>
        <div className="flex items-center space-x-3">
          <span className={`flex items-center gap-1 font-semibold ${isCritical ? 'text-rose-400' : 'text-slate-600'}`}>
            <Volume2 className="w-3.5 h-3.5" /> Buzzer {isCritical ? 'ON' : 'OFF'}
          </span>
          <span className={`flex items-center gap-1 font-semibold ${isCritical ? 'text-rose-400' : 'text-slate-600'}`}>
            <Power className="w-3.5 h-3.5" /> Relay {isCritical ? 'POWER CUT' : 'NORMAL'}
          </span>
        </div>
      </div>

    </div>
  );
};
