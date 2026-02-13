import { useEffect, useRef } from "react";

interface VoiceVisualizerProps {
    isActive: boolean;
    mode: "listening" | "speaking";
}

export const VoiceVisualizer = ({ isActive, mode }: VoiceVisualizerProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!isActive || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;
        const centerY = height / 2;
        const bars = 32;
        const barWidth = width / bars;

        let animationId: number;
        let phase = 0;

        const animate = () => {
            ctx.clearRect(0, 0, width, height);

            const waveFrequency = mode === "listening" ? 0.15 : 0.2;

            for (let i = 0; i < bars; i++) {
                // Create wave effect
                const amplitude = mode === "listening" ? 0.5 : 0.8;
                const offset = mode === "listening" ? i * 0.3 : i * 0.5;

                const barHeight = Math.sin(phase + offset) * height * amplitude + 10;
                const x = i * barWidth;
                const y = centerY - barHeight / 2;

                // Color based on mode
                const color = mode === "listening" ? "#00ff41" : "#00d9ff";
                const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
                gradient.addColorStop(0, color + "00");
                gradient.addColorStop(0.5, color);
                gradient.addColorStop(1, color + "00");

                ctx.fillStyle = gradient;
                ctx.fillRect(x, y, barWidth - 2, barHeight);
            }

            phase += waveFrequency;
            animationId = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
        };
    }, [isActive, mode]);

    if (!isActive) return null;

    return (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <canvas
                ref={canvasRef}
                width={400}
                height={100}
                className="opacity-60"
                style={{ filter: `drop-shadow(0 0 20px ${mode === "listening" ? "#00ff41" : "#00d9ff"})` }}
            />
        </div>
    );
};
