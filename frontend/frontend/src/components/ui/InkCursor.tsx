import React, { useEffect, useRef, useState } from 'react';

const InkCursor: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const pointsRef = useRef<{ x: number; y: number; age: number; size: number }[]>([]);
    const mouseRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
    const angleRef = useRef(0);
    const [isHovering, setIsHovering] = useState(false);
    const hoverScaleRef = useRef(1);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Hide default cursor on FriendsPage via body style
        document.body.style.cursor = 'none';

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        const handleMouseMove = (e: MouseEvent) => {
            // Calculate movement for brush tilt
            const dx = e.clientX - mouseRef.current.x;
            const dy = e.clientY - mouseRef.current.y;
            const targetAngle = Math.atan2(dy, dx) + Math.PI / 2;

            // Smoothly interpolate angle
            angleRef.current += (targetAngle - angleRef.current) * 0.1;

            mouseRef.current = { x: e.clientX, y: e.clientY };

            // Check if hovering over interactive elements
            const target = e.target as HTMLElement;
            const isInteractable = target.closest('button, a, input, [role="button"]');
            setIsHovering(!!isInteractable);

            const size = (Math.random() * 8 + 4) * hoverScaleRef.current;
            pointsRef.current.push({
                x: e.clientX,
                y: e.clientY,
                age: 0,
                size: size
            });
        };
        window.addEventListener('mousemove', handleMouseMove);

        const animate = () => {
            if (!ctx || !canvas) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Interpolate hover scale
            const targetScale = isHovering ? 1.4 : 1.0;
            hoverScaleRef.current += (targetScale - hoverScaleRef.current) * 0.15;

            // 1. Draw Ink Trails
            for (let i = pointsRef.current.length - 1; i >= 0; i--) {
                const point = pointsRef.current[i];
                point.age += 1;

                if (point.age > 50) {
                    pointsRef.current.splice(i, 1);
                    continue;
                }

                const opacity = (1 - point.age / 50) * 0.6;
                ctx.beginPath();
                ctx.arc(point.x, point.y, point.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(10, 10, 15, ${opacity})`;
                ctx.fill();

                if (point.age < 2 && Math.random() > (isHovering ? 0.7 : 0.9)) {
                    const splashX = point.x + (Math.random() - 0.5) * 40;
                    const splashY = point.y + (Math.random() - 0.5) * 40;
                    ctx.beginPath();
                    ctx.arc(splashX, splashY, Math.random() * 2 * hoverScaleRef.current, 0, Math.PI * 2);
                    ctx.fillStyle = isHovering ? `rgba(212, 175, 55, 0.4)` : `rgba(10, 10, 15, ${Math.random() * 0.4})`;
                    ctx.fill();
                }
            }

            // 2. Draw Core Path
            if (pointsRef.current.length > 2) {
                ctx.beginPath();
                ctx.moveTo(pointsRef.current[0].x, pointsRef.current[0].y);
                for (let i = 1; i < pointsRef.current.length - 1; i++) {
                    const p1 = pointsRef.current[i];
                    const p2 = pointsRef.current[i + 1];
                    const xc = (p1.x + p2.x) / 2;
                    const yc = (p1.y + p2.y) / 2;
                    ctx.quadraticCurveTo(p1.x, p1.y, xc, yc);
                }
                ctx.shadowBlur = isHovering ? 15 : 10;
                ctx.shadowColor = isHovering ? 'rgba(212, 175, 55, 0.5)' : 'rgba(0,0,0,0.5)';
                ctx.strokeStyle = `rgba(20, 20, 30, 0.4)`;
                ctx.lineWidth = 4 * hoverScaleRef.current;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.stroke();
                ctx.shadowBlur = 0;
            }

            // 3. Draw Brush Head (The Cursor)
            const { x, y } = mouseRef.current;
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(angleRef.current);
            ctx.scale(hoverScaleRef.current, hoverScaleRef.current);

            // Hover Glow Aura
            if (isHovering) {
                ctx.shadowBlur = 20;
                ctx.shadowColor = '#D4AF37';
            }

            // Draw Brush Handle (Wood)
            ctx.fillStyle = '#1A1110'; // Dark Ebony wood
            ctx.fillRect(-2, -40, 4, 30);

            // Draw Brush Ferrule (Gold/Jade)
            ctx.fillStyle = isHovering ? '#D4AF37' : '#BDB3A3';
            ctx.fillRect(-3, -15, 6, 8);

            // Draw Brush Tip (Hair)
            const gradient = ctx.createLinearGradient(0, -7, 0, 15);
            gradient.addColorStop(0, isHovering ? '#FFFDF0' : '#E0D8D0');
            gradient.addColorStop(0.4, isHovering ? '#D4AF37' : '#BDB3A3');
            gradient.addColorStop(1, '#15151A');

            ctx.beginPath();
            ctx.moveTo(-4, -7);
            ctx.quadraticCurveTo(-6, 5, 0, 15); // Left curve to point
            ctx.quadraticCurveTo(6, 5, 4, -7); // Right curve
            ctx.closePath();
            ctx.fillStyle = gradient;
            ctx.fill();

            ctx.restore();

            requestAnimationFrame(animate);
        };
        const animationId = requestAnimationFrame(animate);

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            window.removeEventListener('mousemove', handleMouseMove);
            document.body.style.cursor = 'default'; // Restore cursor on unmount
            cancelAnimationFrame(animationId);
        };
    }, [isHovering]);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-[9999]"
            style={{ mixBlendMode: 'normal' }}
        />
    );
};

export default InkCursor;
