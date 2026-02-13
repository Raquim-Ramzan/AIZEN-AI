import { useState, useMemo } from "react";
import { VoiceVisualizer } from "./VoiceVisualizer";

type SphereState = "idle" | "hover" | "listening" | "processing" | "speaking" | "error";

// Color constants
const COLOR_IDLE = "#00d9ff";      // Cyan - default/idle
const COLOR_ACTIVE = "#00ff41";    // Terminal Green - active states
const COLOR_ERROR = "#ff4444";     // Red - error state

interface HolographicSphereProps {
    state: SphereState;
    onActivate: () => void;
    audioLevel?: number;  // 0-1 range from LiveKit VAD
}

export const HolographicSphere = ({ state, onActivate, audioLevel = 0 }: HolographicSphereProps) => {
    const [isHovered, setIsHovered] = useState(false);

    // Check if in active voice cycle (listening -> processing -> speaking)
    const isActiveState = state === "listening" || state === "processing" || state === "speaking";

    const getStateColor = () => {
        // Error state always red
        if (state === "error") return COLOR_ERROR;

        // Active cycle (listening/processing/speaking) = Terminal Green
        if (isActiveState) return COLOR_ACTIVE;

        // Default/Idle = Cyan
        return COLOR_IDLE;
    };

    const getStateText = () => {
        switch (state) {
            case "listening":
                return "LISTENING...";
            case "processing":
                return "PROCESSING...";
            case "speaking":
                return "SPEAKING...";
            case "error":
                return "ERROR";
            default:
                return isHovered ? "" : "CLICK TO ACTIVATE";
        }
    };

    const getAnimationSpeed = () => {
        switch (state) {
            case "listening":
                return "8s";   // Faster when listening
            case "processing":
                return "5s";   // Fastest during processing
            case "speaking":
                return "10s";  // Moderate during speech
            default:
                return isHovered ? "18s" : "20s";
        }
    };

    const color = getStateColor();

    // Audio-reactive scale: base scale 1.0, pulses up to 1.2 based on audioLevel
    // Only pulse when in active state
    const baseScale = isHovered && state === "idle" ? 1.05 : 1.0;
    const audioReactiveScale = isActiveState
        ? baseScale + (audioLevel * 0.2)  // Scale between 1.0 and 1.2
        : baseScale;

    // Clamp scale to prevent over-scaling
    const scale = Math.min(Math.max(audioReactiveScale, 1.0), 1.25);

    // Memoize particles to prevent re-generation on each render
    const particles = useMemo(() => Array.from({ length: 25 }, (_, i) => ({
        id: i,
        angle: (i * 360) / 25,
        radius: 180 + Math.random() * 40,
        delay: Math.random() * 8,
        duration: 8 + Math.random() * 7,
    })), []);


    return (
        <div className="flex flex-col items-center justify-center h-full">
            <div
                className="relative cursor-pointer transition-transform duration-500"
                style={{ transform: `scale(${scale})` }}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onClick={onActivate}
            >
                {/* Background glow */}
                <div
                    className="absolute inset-0 rounded-full blur-[80px] animate-pulse-glow"
                    style={{
                        background: `radial-gradient(circle, ${color}40 0%, transparent 70%)`,
                        width: "500px",
                        height: "500px",
                        top: "50%",
                        left: "50%",
                        transform: "translate(-50%, -50%)",
                    }}
                />

                {/* SVG Container */}
                <svg
                    width="500"
                    height="500"
                    viewBox="0 0 500 500"
                    className="relative"
                    style={{ filter: `drop-shadow(0 0 20px ${color}80)` }}
                >
                    {/* Center core - AIZEN text */}
                    <g className="animate-float">
                        <text
                            x="250"
                            y="250"
                            textAnchor="middle"
                            dominantBaseline="middle"
                            fill={color}
                            fontSize="36"
                            fontWeight="900"
                            fontFamily="Orbitron, sans-serif"
                            letterSpacing="4"
                            className="glow-cyan animate-pulse-glow"
                        >
                            AIZEN
                        </text>
                    </g>

                    {/* Inner ring - 150px diameter, 12 segments */}
                    <g
                        style={{
                            animation: `rotate-slow ${getAnimationSpeed()} linear infinite`,
                            transformOrigin: "250px 250px",
                        }}
                    >
                        {Array.from({ length: 12 }).map((_, i) => {
                            const startAngle = i * 30;
                            const endAngle = startAngle + 25;
                            const start = polarToCartesian(250, 250, 75, endAngle);
                            const end = polarToCartesian(250, 250, 75, startAngle);
                            const opacity = 0.6 + Math.random() * 0.4;

                            return (
                                <path
                                    key={`inner-${i}`}
                                    d={`M ${start.x} ${start.y} A 75 75 0 0 0 ${end.x} ${end.y}`}
                                    fill="none"
                                    stroke={color}
                                    strokeWidth="3"
                                    opacity={opacity}
                                    style={{
                                        filter: `drop-shadow(0 0 8px ${color})`,
                                    }}
                                />
                            );
                        })}
                    </g>

                    {/* Middle ring - 250px diameter, 16 segments */}
                    <g
                        style={{
                            animation: `rotate-reverse-medium ${parseInt(getAnimationSpeed()) + 10}s linear infinite`,
                            transformOrigin: "250px 250px",
                        }}
                    >
                        {Array.from({ length: 16 }).map((_, i) => {
                            const startAngle = i * 22.5;
                            const endAngle = startAngle + (i % 2 === 0 ? 18 : 10);
                            const start = polarToCartesian(250, 250, 125, endAngle);
                            const end = polarToCartesian(250, 250, 125, startAngle);

                            return (
                                <g key={`middle-${i}`}>
                                    <path
                                        d={`M ${start.x} ${start.y} A 125 125 0 0 0 ${end.x} ${end.y}`}
                                        fill="none"
                                        stroke={color}
                                        strokeWidth="4"
                                        opacity="0.7"
                                        style={{
                                            filter: `drop-shadow(0 0 6px ${color})`,
                                        }}
                                    />
                                    {/* Radial markers */}
                                    {i % 4 === 0 && (
                                        <line
                                            x1="250"
                                            y1="250"
                                            x2={250 + 135 * Math.cos((startAngle * Math.PI) / 180)}
                                            y2={250 + 135 * Math.sin((startAngle * Math.PI) / 180)}
                                            stroke={color}
                                            strokeWidth="2"
                                            opacity="0.5"
                                        />
                                    )}
                                </g>
                            );
                        })}
                    </g>

                    {/* Outer ring - 350px diameter, 4 arcs */}
                    <g
                        style={{
                            animation: `rotate-medium ${parseInt(getAnimationSpeed()) + 20}s linear infinite`,
                            transformOrigin: "250px 250px",
                        }}
                    >
                        {[0, 90, 180, 270].map((startAngle, i) => {
                            const endAngle = startAngle + 90;
                            const start = polarToCartesian(250, 250, 175, endAngle);
                            const end = polarToCartesian(250, 250, 175, startAngle);

                            return (
                                <g key={`outer-${i}`}>
                                    <path
                                        d={`M ${start.x} ${start.y} A 175 175 0 0 0 ${end.x} ${end.y}`}
                                        fill="none"
                                        stroke={color}
                                        strokeWidth="2"
                                        opacity="0.5"
                                        style={{
                                            filter: `drop-shadow(0 0 4px ${color})`,
                                        }}
                                    />
                                    {/* HUD markers */}
                                    <line
                                        x1={250 + 175 * Math.cos((startAngle * Math.PI) / 180)}
                                        y1={250 + 175 * Math.sin((startAngle * Math.PI) / 180)}
                                        x2={250 + 185 * Math.cos((startAngle * Math.PI) / 180)}
                                        y2={250 + 185 * Math.sin((startAngle * Math.PI) / 180)}
                                        stroke={color}
                                        strokeWidth="2"
                                        opacity="0.6"
                                    />
                                </g>
                            );
                        })}
                    </g>

                    {/* Orbital particles */}
                    {particles.map((particle) => (
                        <circle
                            key={particle.id}
                            cx="250"
                            cy="250"
                            r="3"
                            fill={color}
                            opacity="0.8"
                            style={{
                                filter: `drop-shadow(0 0 4px ${color})`,
                                animation: `particle-float ${particle.duration}s ease-in-out infinite`,
                                animationDelay: `${particle.delay}s`,
                            }}
                            transform={`translate(${particle.radius * Math.cos((particle.angle * Math.PI) / 180)}, ${particle.radius * Math.sin((particle.angle * Math.PI) / 180)
                                })`}
                        />
                    ))}

                    {/* Breathing glow for listening state */}
                    {state === "listening" && (
                        <circle
                            cx="250"
                            cy="250"
                            r="200"
                            fill="none"
                            stroke={color}
                            strokeWidth="3"
                            className="animate-breathe"
                            style={{ transformOrigin: "250px 250px" }}
                        />
                    )}

                    {/* Processing spinner */}
                    {state === "processing" && (
                        <g
                            style={{
                                animation: "processing-spin 0.8s linear infinite",
                                transformOrigin: "250px 250px",
                            }}
                        >
                            <circle cx="250" cy="60" r="8" fill={color} opacity="0.9" />
                            <circle cx="250" cy="60" r="4" fill="#ffffff" opacity="0.6" />
                        </g>
                    )}

                    {/* Ripple effect for listening state */}
                    {state === "listening" && (
                        <circle
                            cx="250"
                            cy="250"
                            r="80"
                            fill="none"
                            stroke={color}
                            strokeWidth="2"
                            opacity="0.6"
                            className="animate-ripple"
                            style={{ transformOrigin: "250px 250px" }}
                        />
                    )}

                    {/* Speaking wave bars */}
                    {state === "speaking" && (
                        <g>
                            {[-30, -15, 0, 15, 30].map((offset, i) => (
                                <rect
                                    key={`wave-${i}`}
                                    x={245 + offset}
                                    y="350"
                                    width="6"
                                    height="20"
                                    fill={color}
                                    opacity="0.7"
                                    rx="3"
                                    style={{
                                        animation: `wave-pulse 0.5s ease-in-out infinite`,
                                        animationDelay: `${i * 0.1}s`,
                                        transformOrigin: "center bottom",
                                    }}
                                />
                            ))}
                        </g>
                    )}
                </svg>
            </div>

            {/* Voice visualizer overlay */}
            {(state === "listening" || state === "speaking") && (
                <VoiceVisualizer
                    isActive={true}
                    mode={state as "listening" | "speaking"}
                />
            )}

            {/* State text */}
            <div className="mt-8 text-center">
                <p
                    className="text-sm font-aldrich tracking-widest uppercase"
                    style={{
                        color: color,
                        textShadow: `0 0 10px ${color}`,
                    }}
                >
                    {getStateText()}
                </p>
            </div>
        </div>
    );
};

// Helper function to convert polar coordinates to cartesian
function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
        x: centerX + radius * Math.cos(angleInRadians),
        y: centerY + radius * Math.sin(angleInRadians),
    };
}
