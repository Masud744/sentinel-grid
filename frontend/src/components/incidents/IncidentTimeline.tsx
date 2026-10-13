import React, { useState } from 'react';
import { Search, Filter, Calendar, Clock, CheckCircle2, AlertOctagon, User, ChevronRight, X } from 'lucide-react';

export interface IncidentRecord {
  id: string;
  zone_id: string;
  zone_name: string;
  risk_score: number;
  state: string;
  cause: string;
  opened_at: string;
  resolved_at?: string;
  acknowledgement?: {
    acknowledged_by: string;
    acknowledged_at: string;
  };
}

interface IncidentTimelineProps {
  incidents: IncidentRecord[];
  onAcknowledge?: (incidentId: string) => void;
  canAcknowledge?: boolean;
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({ incidents, onAcknowledge, canAcknowledge }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [stateFilter, setStateFilter] = useState('ALL');
  const [selectedIncident, setSelectedIncident] = useState<IncidentRecord | null>(null);

  const filteredIncidents = incidents.filter((inc) => {
    const matchesSearch =
      inc.zone_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.cause.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesState = stateFilter === 'ALL' || inc.state === stateFilter;
    return matchesSearch && matchesState;
  });

  return (
    <div className="space-y-6">
      
      {/* Search & Filter Bar */}
      <div className="glass-panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by zone name, cause, or incident ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        <div className="flex items-center space-x-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <div className="flex bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs">
            {['ALL', 'CRITICAL', 'WARNING', 'RESOLVED'].map((st) => (
              <button
                key={st}
                onClick={() => setStateFilter(st)}
                className={`px-3 py-1.5 rounded-md font-semibold transition-all ${
                  stateFilter === st
                    ? 'bg-cyan-500 text-slate-950 shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Incident List Cards */}
      <div className="space-y-3">
        {filteredIncidents.length === 0 ? (
          <div className="glass-panel p-8 text-center text-slate-400">
            No incidents matched your query filter.
          </div>
        ) : (
          filteredIncidents.map((inc) => (
            <div
              key={inc.id}
              onClick={() => setSelectedIncident(inc)}
              className="glass-card p-4 flex items-center justify-between cursor-pointer hover:border-cyan-500/50"
            >
              <div className="flex items-center space-x-4">
                <div className={`p-2.5 rounded-xl ${
                  inc.state === 'CRITICAL'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : inc.state === 'WARNING'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  <AlertOctagon className="w-5 h-5" />
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="font-bold text-white text-sm">{inc.zone_name}</h4>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-extrabold ${
                      inc.state === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' : inc.state === 'WARNING' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                    }`}>
                      {inc.state} ({inc.risk_score.toFixed(1)})
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5">{inc.cause}</p>
                  <div className="flex items-center space-x-4 text-[11px] text-slate-400 mt-1">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> {new Date(inc.opened_at).toLocaleString()}
                    </span>
                    {inc.acknowledgement && (
                      <span className="text-cyan-400 flex items-center gap-1 font-medium">
                        <User className="w-3 h-3" /> Ack: {inc.acknowledgement.acknowledged_by}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {canAcknowledge && inc.state !== 'RESOLVED' && !inc.acknowledgement && onAcknowledge && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onAcknowledge(inc.id);
                    }}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg shadow transition-all"
                  >
                    Ack
                  </button>
                )}
                <ChevronRight className="w-5 h-5 text-slate-600" />
              </div>
            </div>
          ))
        )}
      </div>

      {/* Incident Detail Drawer / Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel p-6 max-w-lg w-full border-slate-700 shadow-2xl relative">
            <button
              onClick={() => setSelectedIncident(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold text-white mb-1">Incident State History</h3>
            <p className="text-xs text-slate-400 mb-4">ID: {selectedIncident.id}</p>

            <div className="space-y-4 bg-slate-950/80 p-4 rounded-xl border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block font-semibold">Zone:</span>
                <span className="text-slate-200 font-bold">{selectedIncident.zone_name}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Peak Risk Score:</span>
                <span className="text-rose-400 font-extrabold text-base">{selectedIncident.risk_score.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Primary Cause:</span>
                <span className="text-slate-200">{selectedIncident.cause}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Opened At:</span>
                <span className="text-slate-300">{new Date(selectedIncident.opened_at).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Status:</span>
                <span className="text-slate-200 font-bold">{selectedIncident.resolved_at ? `Resolved at ${new Date(selectedIncident.resolved_at).toLocaleString()}` : 'Active Incident'}</span>
              </div>
              {selectedIncident.acknowledgement && (
                <div className="pt-2 border-t border-slate-800">
                  <span className="text-slate-500 block font-semibold">Acknowledgement:</span>
                  <span className="text-cyan-400 font-medium">
                    By {selectedIncident.acknowledgement.acknowledged_by} at {new Date(selectedIncident.acknowledgement.acknowledged_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedIncident(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
