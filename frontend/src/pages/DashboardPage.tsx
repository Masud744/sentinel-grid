import React, { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '../utils/api';
import { Header } from '../components/common/Header';
import { ZoneCard } from '../components/dashboard/ZoneCard';
import { PriorityQueue } from '../components/dashboard/PriorityQueue';
import { NotificationToastStack, ToastAlert } from '../components/dashboard/NotificationToast';
import { useWebSocket } from '../context/WebSocketContext';
import { Zone } from '../types';

interface ZonesResponse {
  zones: Zone[];
  priorityQueue: any[];
}

const fetchZonesData = async (): Promise<ZonesResponse> => {
  const { data } = await axiosInstance.get('/zones');
  if (Array.isArray(data)) {
    return { zones: data, priorityQueue: [] };
  }
  return {
    zones: data.zones || [],
    priorityQueue: data.priority_queue || [],
  };
};

const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { lastMessage, isConnected } = useWebSocket();
  const [toastAlerts, setToastAlerts] = useState<ToastAlert[]>([]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['zones'],
    queryFn: fetchZonesData,
    refetchInterval: 5000, // fallback polling every 5s
  });

  // Listen for WebSocket live broadcasts and instantly update grid state
  useEffect(() => {
    if (!lastMessage) return;

    // Immediately trigger a light refetch on any WS event
    queryClient.invalidateQueries({ queryKey: ['zones'] });

    // Handle warning/critical alert toasts
    if (lastMessage.event === 'ZONE_TELEMETRY_UPDATED' || lastMessage.event === 'INCIDENT_ESCALATED') {
      const payload = lastMessage.data;
      if (payload && (payload.state === 'CRITICAL' || payload.state === 'WARNING')) {
        const newToast: ToastAlert = {
          id: `${payload.zone_id}-${Date.now()}`,
          incidentId: payload.incident_id,
          zoneName: payload.zone_name,
          state: payload.state,
          riskScore: payload.risk_score,
          cause: payload.cause || `Elevated Risk (${payload.risk_score?.toFixed(1)})`,
          openedAt: new Date().toISOString(),
        };

        setToastAlerts((prev) => {
          // Avoid duplicate toasts for same zone within 5s
          const exists = prev.some(t => t.zoneName === newToast.zoneName && t.state === newToast.state);
          if (exists) return prev;
          return [newToast, ...prev].slice(0, 3); // keep max 3 toasts
        });
      }
    }
  }, [lastMessage, queryClient]);

  const handleDismissToast = (id: string) => {
    setToastAlerts((prev) => prev.filter((t) => t.id !== id));
  };

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-slate-950 text-slate-300">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500 mb-4"></div>
        <span className="text-sm font-medium tracking-wide">Connecting to Campus Safety Grid...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-slate-950 text-rose-400 p-6 text-center">
        <h2 className="text-xl font-bold mb-2">Campus Grid Connection Offline</h2>
        <p className="text-sm text-slate-400 max-w-md">Failed to retrieve telemetry data from the backend risk engine.</p>
      </div>
    );
  }

  const zones = data?.zones || [];
  const priorityQueue = data?.priorityQueue || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <Header />
      
      <main className="p-6 max-w-7xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-wide">
              Campus Multi-Zone Safety Dashboard
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Real-time multi-sensor telemetry, risk score fusion & automated actuation state
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs bg-slate-900/90 border border-slate-800 px-4 py-2 rounded-xl">
            <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-500'}`}></span>
            <span className="text-slate-300 font-semibold">
              {isConnected ? `${zones.length} Zones Monitored (Live Feed)` : 'Connecting WebSocket...'}
            </span>
          </div>
        </div>

        {/* Priority Response Queue (Visible when there are critical hazards) */}
        <PriorityQueue items={priorityQueue} />

        {/* Live Zones Grid */}
        <div>
          <h2 className="text-lg font-bold text-white mb-4 tracking-wide flex items-center gap-2">
            Monitored Campus Zones
          </h2>
          <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4">
            {zones.map((zone) => (
              <ZoneCard key={zone.id} zone={zone} />
            ))}
          </div>
        </div>
      </main>

      {/* Notification Toast Stack */}
      <NotificationToastStack
        alerts={toastAlerts}
        onDismiss={handleDismissToast}
        onAcknowledge={() => {}}
        canAcknowledge={false}
      />
    </div>
  );
};

export default DashboardPage;
