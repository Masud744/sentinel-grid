import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TrendingSparklineProps {
  isTrendingUp?: boolean;
  slope?: number;
}

export const TrendingSparkline: React.FC<TrendingSparklineProps> = ({ isTrendingUp, slope = 0.0 }) => {
  if (isTrendingUp) {
    return (
      <div className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold">
        <TrendingUp className="w-3.5 h-3.5 animate-bounce" />
        <span>Trending Up (+{slope.toFixed(2)}/frame)</span>
      </div>
    );
  }

  if (slope < -0.2) {
    return (
      <div className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
        <TrendingDown className="w-3.5 h-3.5" />
        <span>Stable / Cooling ({slope.toFixed(2)})</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800/60 text-slate-400 text-xs">
      <Minus className="w-3 h-3" />
      <span>Steady State</span>
    </div>
  );
};
