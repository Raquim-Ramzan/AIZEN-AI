import { useEffect, useRef } from "react";

export const BackgroundEffects = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Create stars for parallax starfield
        const stars: Array<{ x: number; y: number; z: number; size: number }> = [];
        for (let i = 0; i < 200; i++) {
            stars.push({
                x: Math.random() * canvas.width - canvas.width / 2,
                y: Math.random() * canvas.height - canvas.height / 2,
                z: Math.random() * canvas.width,
                size: Math.random() * 2,
            });
        }

        let animationId: number;

        const animate = () => {
            ctx.fillStyle = "rgba(0, 0, 0, 0.1)";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw stars with parallax effect
            stars.forEach((star) => {
                star.z -= 2;
                if (star.z <= 0) {
                    star.z = canvas.width;
                }

                const x = (star.x / star.z) * canvas.width + canvas.width / 2;
                const y = (star.y / star.z) * canvas.height + canvas.height / 2;
                const s = (1 - star.z / canvas.width) * star.size;

                ctx.fillStyle = "rgba(255, 255, 255, " + (1 - star.z / canvas.width) + ")";
                ctx.fillRect(x, y, s, s);
            });

            animationId = requestAnimationFrame(animate);
        };

        animate();

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener("resize", handleResize);

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener("resize", handleResize);
        };
    }, []);

    return (
        <>
            {/* Starfield canvas - Layer 1 (deepest) */}
            <canvas
                ref={canvasRef}
                className="fixed inset-0 pointer-events-none"
                style={{ zIndex: 0 }}
            />

            {/* Atmospheric gradient drift - Layer 2 */}
            <div
                className="fixed inset-0 pointer-events-none opacity-30 animate-atmospheric-drift"
                style={{
                    background: `radial-gradient(circle at 30% 40%, rgba(0, 217, 255, 0.08) 0%, transparent 50%),
                                radial-gradient(circle at 70% 60%, rgba(0, 255, 65, 0.06) 0%, transparent 50%)`,
                    zIndex: 0,
                }}
            />

            {/* Grid overlay - Layer 3 */}
            <div
                className="fixed inset-0 pointer-events-none"
                style={{
                    backgroundImage: `
            linear-gradient(rgba(0, 217, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 217, 255, 0.03) 1px, transparent 1px)
          `,
                    backgroundSize: "50px 50px",
                    zIndex: 1,
                }}
            />

            {/* Vignette - Layer 4 */}
            <div
                className="fixed inset-0 pointer-events-none"
                style={{
                    background: "radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.6) 100%)",
                    zIndex: 1,
                }}
            />

            {/* Scanlines - Layer 5 (foreground) */}
            <div className="fixed inset-0 pointer-events-none scanlines" style={{ zIndex: 1 }} />
        </>
    );
};
