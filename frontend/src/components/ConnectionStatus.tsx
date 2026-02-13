import { useState, useEffect } from "react";
import { Wifi, WifiOff, Activity } from "lucide-react";

type ConnectionState = "connected" | "connecting" | "disconnected" | "error";

interface ConnectionStatusProps {
    status?: ConnectionState;
}

export const ConnectionStatus = ({ status = "connected" }: ConnectionStatusProps) => {
    const [pingTime, setPingTime] = useState(0);

    useEffect(() => {
        // Simulate ping time
        const interval = setInterval(() => {
            setPingTime(Math.floor(Math.random() * 50) + 20);
        }, 2000);

        return () => clearInterval(interval);
    }, []);

    const getStatusConfig = () => {
        switch (status) {
            case "connected":
                return {
                    icon: <Wifi className="w-4 h-4" />,
                    text: "CONNECTED",
                    color: "text-accent",
                    dotColor: "bg-accent",
                    showPing: true,
                };
            case "connecting":
                return {
                    icon: <Activity className="w-4 h-4 animate-pulse" />,
                    text: "CONNECTING",
                    color: "text-primary",
                    dotColor: "bg-primary",
                    showPing: false,
                };
            case "error":
                return {
                    icon: <WifiOff className="w-4 h-4" />,
                    text: "ERROR",
                    color: "text-destructive",
                    dotColor: "bg-destructive",
                    showPing: false,
                };
            case "disconnected":
                return {
                    icon: <WifiOff className="w-4 h-4" />,
                    text: "DISCONNECTED",
                    color: "text-destructive",
                    dotColor: "bg-destructive",
                    showPing: false,
                };
        }
    };

    const config = getStatusConfig();

    return (
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-black/60 border border-primary/20 backdrop-blur-sm">
            <div className={`${config.dotColor} w-2 h-2 rounded-full ${status === "connected" ? "animate-pulse-glow" : ""}`} />
            <div className={`${config.color}`}>{config.icon}</div>
            <div className="flex flex-col">
                <span className={`text-xs font-aldrich ${config.color} tracking-wider uppercase`}>
                    {config.text}
                </span>
                {config.showPing && (
                    <span className="text-[10px] text-muted-foreground font-quantico">
                        {pingTime}ms
                    </span>
                )}
            </div>
        </div>
    );
};
