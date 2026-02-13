import { Brain, Check } from "lucide-react";
import { useState, useEffect } from "react";

interface MemoryIndicatorProps {
    isLearning: boolean;
    message?: string;
}

export const MemoryIndicator = ({ isLearning, message }: MemoryIndicatorProps) => {
    const [show, setShow] = useState(false);

    useEffect(() => {
        if (isLearning) {
            setShow(true);
        } else {
            const timer = setTimeout(() => setShow(false), 3000);
            return () => clearTimeout(timer);
        }
    }, [isLearning]);

    if (!show) return null;

    return (
        <div className="fixed bottom-24 right-8 z-40 animate-slide-in-right">
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-black/90 border-2 border-primary/30 backdrop-blur-md shadow-[0_0_20px_rgba(0,217,255,0.3)]">
                {isLearning ? (
                    <>
                        <Brain className="w-5 h-5 text-primary animate-pulse" />
                        <div className="flex flex-col">
                            <span className="text-sm font-aldrich text-primary uppercase tracking-wide">
                                Learning
                            </span>
                            <span className="text-xs text-muted-foreground font-quantico">
                                {message || "Storing to core memory..."}
                            </span>
                        </div>
                        <div className="flex gap-1 ml-2">
                            <div className="w-1 h-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                            <div className="w-1 h-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                            <div className="w-1 h-1 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
                        </div>
                    </>
                ) : (
                    <>
                        <Check className="w-5 h-5 text-accent" />
                        <div className="flex flex-col">
                            <span className="text-sm font-aldrich text-accent uppercase tracking-wide">
                                Learned
                            </span>
                            <span className="text-xs text-muted-foreground font-quantico">
                                {message || "Saved to memory"}
                            </span>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
