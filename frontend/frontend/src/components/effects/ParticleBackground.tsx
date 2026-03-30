import { useEffect, useRef } from 'react';

export type ParticleType = 'fire' | 'water' | 'wood' | 'metal' | 'earth' | 'air' | 'eastern' | 'western';

interface ParticleBackgroundProps {
    type: ParticleType;
    className?: string;
    opacity?: number;
}

interface Particle {
    x: number;
    y: number;
    size: number;
    speedX: number;
    speedY: number;
    opacity: number;
    color: string;
    life: number;
    maxLife: number;
    angle?: number;      // For rotation (leaves)
    angleSpeed?: number; // For rotation speed
    length?: number;     // For rain streaks
}

const ParticleBackground = ({ type, className = "", opacity = 1 }: ParticleBackgroundProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;
        let particles: Particle[] = [];

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initParticles();
        };

        const createParticle = (): Particle => {
            const w = canvas.width;
            const h = canvas.height;

            // Defaults
            let p: Particle = {
                x: Math.random() * w,
                y: Math.random() * h,
                size: Math.random() * 2 + 1,
                speedX: 0,
                speedY: 0,
                opacity: Math.random(),
                color: '255, 255, 255', // Default white
                life: Math.random() * 100,
                maxLife: 100
            };

            switch (type) {
                case 'fire':
                    // INTENSE FIRE: Faster, bigger, more chaotic
                    p.x = Math.random() * w;
                    p.y = h + Math.random() * 50; // Start below
                    p.size = Math.random() * 8 + 4; // Larger
                    p.speedY = -Math.random() * 5 - 2; // Up extremely fast
                    p.speedX = (Math.random() - 0.5) * 3; // Chaotic wind
                    // Mix of Orange, Red, Yellow
                    const randFire = Math.random();
                    if (randFire > 0.6) p.color = '255, 60, 0';   // Deep Red
                    else if (randFire > 0.3) p.color = '255, 140, 0'; // Orange
                    else p.color = '255, 220, 50'; // Yellow
                    p.opacity = Math.random() * 0.7 + 0.3; // High opacity
                    p.maxLife = 40 + Math.random() * 40;
                    break;

                case 'water':
                    // HEAVY RAIN: Fast streaks
                    p.x = Math.random() * w;
                    p.y = -Math.random() * 100; // Start above
                    p.size = Math.random() * 1.5 + 0.5; // Thinner
                    p.length = Math.random() * 20 + 10; // Rain streak length
                    p.speedY = Math.random() * 10 + 15; // Very fast down
                    p.speedX = -2; // Slight wind slant
                    p.color = '160, 210, 255'; // Icy Blue
                    p.opacity = Math.random() * 0.5 + 0.3;
                    break;

                case 'wood':
                    // FALLING LEAVES: Spinning, floating
                    p.x = Math.random() * w;
                    p.y = Math.random() * h;
                    p.size = Math.random() * 12 + 8; // MUCH Bigger leaves (8-20px)
                    p.speedY = Math.random() * 1.5 + 0.8; // Fall a bit faster due to weight
                    p.speedX = (Math.random() - 0.5) * 4; // Sway wider
                    p.angle = Math.random() * 360;
                    p.angleSpeed = (Math.random() - 0.5) * 5; // Spin speed
                    // Green shades
                    const randWood = Math.random();
                    if (randWood > 0.7) p.color = '100, 230, 100'; // Bright Green
                    else if (randWood > 0.4) p.color = '34, 197, 94'; // Emerald
                    else p.color = '167, 243, 208'; // Pale Leaf
                    p.opacity = Math.random() * 0.6 + 0.2;
                    break;

                case 'metal':
                    // SPARKLES: Sharp, blinking, metallic -> NOW MORE DYNAMIC
                    p.size = Math.random() * 6 + 3; // Much bigger (3-9px)
                    p.speedX = (Math.random() - 0.5) * 1.5; // Faster movement
                    p.speedY = (Math.random() - 0.5) * 1.5;
                    p.color = '240, 240, 255'; // Silver/White
                    p.opacity = Math.random();
                    p.angle = Math.random() * 360; // Add rotation
                    p.angleSpeed = (Math.random() - 0.5) * 10; // Fast spin
                    break;

                case 'earth':
                    // RISING DUST / FLOATING ROCKS -> NOW MORE DYNAMIC
                    p.size = Math.random() * 10 + 4; // Much bigger (4-14px)
                    p.speedY = -Math.random() * 1.5 - 0.5; // Faster float UP
                    p.speedX = (Math.random() - 0.5) * 2; // More horizontal wander
                    p.color = '194, 161, 120'; // Sand/Beige color
                    p.opacity = Math.random() * 0.6 + 0.2;
                    p.angle = Math.random() * 360; // Rotating rocks
                    p.angleSpeed = (Math.random() - 0.5) * 2;
                    break;

                case 'air':
                    // SHARP CUTTING WIND (Extreme)
                    p.x = -Math.random() * w; // Start way off to the left
                    p.y = Math.random() * h;

                    // Thinner and Longer
                    p.size = Math.random() * 1.2 + 0.3; // Very thin (0.3 - 1.5px)
                    p.length = Math.random() * 300 + 100; // Very Long streaks (100-400px)

                    // Very Fast but slightly reduced
                    p.speedX = Math.random() * 15 + 15; // 15-30 speed (was 25-45)
                    p.speedY = (Math.random() - 0.5) * 0.2; // Stable Y

                    // Pure White / Icy
                    p.color = '240, 250, 255';
                    p.opacity = Math.random() * 0.5 + 0.3;
                    break;

                case 'eastern':
                    p.speedY = Math.random() * -0.5 - 0.2;
                    p.color = '251, 191, 36';
                    p.opacity = Math.random() * 0.5 + 0.1;
                    break;

                case 'western':
                default:
                    p.size = Math.random() * 2;
                    p.speedX = (Math.random() - 0.5) * 0.2;
                    p.speedY = (Math.random() - 0.5) * 0.2;
                    p.color = '255, 255, 255';
                    break;
            }

            return p;
        };

        const initParticles = () => {
            particles = [];
            let count = 60;
            if (type === 'fire') count = 150; // MORE FIRE
            if (type === 'water') count = 200; // MORE RAIN
            if (type === 'wood') count = 40;  // LEAVES
            if (type === 'western' || type === 'metal') count = 80;
            if (type === 'earth') count = 60;
            if (type === 'air') count = 120; // High density for wind gusts

            for (let i = 0; i < count; i++) {
                particles.push(createParticle());
                // Pre-warm positions
                particles[i].x = Math.random() * canvas.width;
                particles[i].y = Math.random() * canvas.height;
            }
        };

        const draw = () => {
            if (!canvas || !ctx) return;

            // Trails for motion blur effect
            if (type === 'fire' || type === 'water') {
                ctx.fillStyle = `rgba(0, 0, 0, 0.2)`; // Stronger trails
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            } else {
                // For Air (Sharp), Wood, Earth, Metal -> Clear completely for sharpness
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }

            particles.forEach((p, index) => {
                ctx.beginPath();

                const currentOpacity = p.opacity * opacity;
                ctx.fillStyle = `rgba(${p.color}, ${currentOpacity})`;

                if (type === 'wood' || type === 'earth') {
                    // Draw Leaf (Wood) or Rock (Earth)
                    ctx.save();
                    ctx.translate(p.x, p.y);
                    ctx.rotate((p.angle || 0) * Math.PI / 180);

                    if (type === 'wood') {
                        ctx.ellipse(0, 0, p.size, p.size * 0.4, 0, 0, Math.PI * 2);
                    } else {
                        // Earth: Draw irregular rock/debris (roughly square/jagged)
                        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
                    }

                    ctx.restore();
                    ctx.fill();

                    // Update Angle
                    if (p.angle !== undefined && p.angleSpeed !== undefined) {
                        p.angle += p.angleSpeed;
                    }
                } else if (type === 'water') {
                    // Draw Rain Streak
                    ctx.strokeStyle = `rgba(${p.color}, ${currentOpacity})`;
                    ctx.lineWidth = p.size;
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p.x + (p.speedX * 2), p.y + (p.length || 10)); // Stretch based on speed
                    ctx.stroke();
                } else if (type === 'air') {
                    // WIND STREAK (Sharp line)
                    // If p.length is undefined (backup), give it a value
                    const len = p.length || 100;

                    const grad = ctx.createLinearGradient(p.x, p.y, p.x + len, p.y);
                    grad.addColorStop(0, `rgba(${p.color}, 0)`);
                    grad.addColorStop(0.1, `rgba(${p.color}, ${currentOpacity})`); // Sharp attack
                    grad.addColorStop(0.8, `rgba(${p.color}, ${currentOpacity * 0.5})`);
                    grad.addColorStop(1, `rgba(${p.color}, 0)`); // Long tail fade

                    ctx.fillStyle = grad;
                    ctx.fillRect(p.x, p.y, len, p.size);

                } else if (type === 'metal') {
                    // Draw Sparkle (Diamond/Star)
                    ctx.save();
                    ctx.translate(p.x, p.y);
                    // Blinking effect + Rotation
                    const scale = 0.5 + Math.abs(Math.sin(Date.now() * 0.005 + p.x * 0.1)) * 0.5;
                    ctx.scale(scale, scale);
                    ctx.rotate((p.angle || 0) * Math.PI / 180); // Rotate the sparkle

                    ctx.moveTo(0, -p.size * 2);
                    ctx.lineTo(p.size, 0);
                    ctx.lineTo(0, p.size * 2);
                    ctx.lineTo(-p.size, 0);
                    ctx.closePath();
                    ctx.fill();
                    ctx.restore();

                    // Update Angle
                    if (p.angle !== undefined && p.angleSpeed !== undefined) {
                        p.angle += p.angleSpeed;
                    }
                } else {
                    // Default Circle
                    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Physics Update
                p.x += p.speedX;
                p.y += p.speedY;

                // Fire Specific
                if (type === 'fire') {
                    p.opacity -= 0.015; // Fade out faster
                    p.size -= 0.05;
                    p.x += Math.sin(p.y * 0.1) * 0.5; // Wiggle
                    if (p.size <= 0 || p.opacity <= 0) {
                        particles[index] = createParticle(); // Respawn
                    }
                }

                // Earth Specific
                if (type === 'earth') {
                    p.x += Math.sin(p.y * 0.02) * 0.1; // Gentle sway
                }

                // Wrap or Respawn Logic
                if (type === 'water') {
                    if (p.y > canvas.height) { // Rain hits bottom
                        p.y = -50;
                        p.x = Math.random() * canvas.width;
                    }
                } else if (type === 'air') {
                    if (p.x > canvas.width + 400) { // Allow long streaks to fully exit
                        p.x = -Math.random() * 200 - 400; // Reset far left
                        p.y = Math.random() * canvas.height;
                    }
                } else {
                    if (p.y < -50 && p.speedY < 0) { p.y = canvas.height + 50; p.x = Math.random() * canvas.width; }
                    if (p.y > canvas.height + 50 && p.speedY > 0) { p.y = -50; p.x = Math.random() * canvas.width; }
                    if (p.x < -100) p.x = canvas.width + 100;
                    if (p.x > canvas.width + 100) p.x = -100;
                }

                // Random Respawn to keep it fresh
                if (type !== 'fire' && type !== 'water' && Math.random() < 0.002) {
                    particles[index] = createParticle();
                }
            });

            animationFrameId = requestAnimationFrame(draw);
        };

        window.addEventListener('resize', resize);
        resize();
        draw();

        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animationFrameId);
        };
    }, [type, opacity]);

    return <canvas ref={canvasRef} className={`absolute inset-0 pointer-events-none ${className}`} />;
};

export default ParticleBackground;
