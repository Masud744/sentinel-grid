import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: any;
}

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  lastMessage: null,
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<any>(null);

  useEffect(() => {
    let reconnectTimer: any = null;
    let isComponentMounted = true;

    const connectWS = () => {
      if (!isComponentMounted) return;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Use window.location.host so it works via Vite proxy (/ws) or direct port
      const host = window.location.port === '5173'
        ? `${window.location.hostname}:8000`
        : window.location.host;
      const wsUrl = `${protocol}//${host}/ws/updates`;

      console.log(`[SCS-RG WS] Connecting to ${wsUrl}...`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isComponentMounted) return;
        console.log('[SCS-RG WS] Connected successfully to backend live telemetry feed');
        setIsConnected(true);

        // Start ping heartbeat every 15s to prevent proxy/idle timeouts
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        if (!isComponentMounted) return;
        if (event.data === "pong") return; // ignore heartbeat responses

        try {
          const parsed = JSON.parse(event.data);
          setLastMessage(parsed);
        } catch (e) {
          console.error('[SCS-RG WS] Error parsing message payload:', e);
        }
      };

      ws.onclose = (event) => {
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        if (!isComponentMounted) return;

        console.log(`[SCS-RG WS] Connection closed (code: ${event.code}). Reconnecting in 3s...`);
        setIsConnected(false);
        reconnectTimer = setTimeout(connectWS, 3000);
      };

      ws.onerror = (error) => {
        console.error('[SCS-RG WS] Network error encountered:', error);
      };
    };

    connectWS();

    return () => {
      isComponentMounted = false;
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ isConnected, lastMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
