/**
 * Offline Fallback Component
 * Shows when backend is not available
 */

import { ServerOff, RefreshCw } from "lucide-react";

interface OfflineFallbackProps {
    onRetry?: () => void;
}

export const OfflineFallback = ({ onRetry }: OfflineFallbackProps) => {
    return (
        <div className="flex flex-col items-center justify-center h-full gap-6 p-8">
            <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
                <ServerOff className="w-24 h-24 text-primary relative z-10" />
            </div>

            <div className="text-center space-y-2">
                <h2 className="text-2xl font-aldrich text-primary tracking-wider">
                    BACKEND OFFLINE
                </h2>
                <p className="text-muted-foreground font-quantico max-w-md">
                    The AIZEN backend server is not responding. Please start the backend server and try again.
                </p>
            </div>

            {onRetry && (
                <button
                    onClick={onRetry}
                    className="flex items-center gap-2 px-6 py-3 bg-primary/20 hover:bg-primary/30 border border-primary/40 rounded-lg transition-all duration-300 group"
                >
                    <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                    <span className="font-aldrich text-sm tracking-wider">RETRY CONNECTION</span>
                </button>
            )}

            <div className="mt-8 p-4 bg-black/40 border border-primary/20 rounded-lg max-w-lg">
                <p className="text-xs font-quantico text-muted-foreground text-center">
                    <span className="text-primary">Tip:</span> Start the backend with:{" "}
                    <code className="bg-black/60 px-2 py-1 rounded text-accent">
                        python -m app.main
                    </code>
                </p>
            </div>
        </div>
    );
};
