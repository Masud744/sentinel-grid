import React from 'react';
import { AlertOctagon, X, CheckCircle, ShieldAlert } from 'lucide-react';

export interface ToastAlert {
  id: string;
  incidentId?: string;
  zoneName: string;
  state: string;
  riskScore: number;
  cause: string;
  openedAt: string;
  acknowledged?: boolean;
  acknowledgedBy?: string;
}

interface NotificationToastProps {
  alerts: ToastAlert[];
  onDismiss: (id: string) => void;
  onAcknowledge: (incidentId: string) => void;
  canAcknowledge: boolean;
}

export const NotificationToastStack: React.FC<NotificationToastProps> = ({
  alerts,
  onDismiss,
  onAcknowledge,
  canAcknowledge
}) => {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col space-y-3 max-w-md w-full px-4 sm:px-0">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`p-4 rounded-xl border shadow-2xl backdrop-blur-lg transition-all duration-300 transform translate-y-0 ${
            alert.acknowledged
              ? 'bg-slate-900/90 border-slate-700 text-slate-300'
              : 'bg-rose-950/90 border-rose-500 text-white pulse-critical'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <div className={`p-2 rounded-lg ${alert.acknowledged ? 'bg-slate-800 text-slate-400' : 'bg-rose-600 text-white'}`}>
                <AlertOctagon className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="font-bold text-sm tracking-wide">{alert.zoneName}</h4>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-extrabold uppercase ${
                    alert.acknowledged ? 'bg-slate-800 text-slate-400' : 'bg-rose-500/30 text-rose-200 border border-rose-400/40'
                  }`}>
                    {alert.state} ({alert.riskScore.toFixed(1)})
                  </span>
                </div>
                <p className="text-xs text-rose-200/90 mt-1 font-medium">{alert.cause}</p>
                
                {alert.acknowledged ? (
                  <p className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1 font-semibold">
                    <CheckCircle className="w-3.5 h-3.5" /> Acknowledged by {alert.acknowledgedBy}
                  </p>
                ) : (
                  <div className="mt-3 flex items-center space-x-2">
                    {canAcknowledge && alert.incidentId && (
                      <button
                        onClick={() => onAcknowledge(alert.incidentId!)}
                        className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg shadow transition-all flex items-center gap-1"
                      >
                        <ShieldAlert className="w-3.5 h-3.5" /> Acknowledge Alert
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={() => onDismiss(alert.id)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
