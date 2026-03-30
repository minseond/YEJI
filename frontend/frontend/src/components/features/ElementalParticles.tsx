import { motion } from 'framer-motion';
import { useMemo } from 'react';

type ElementType = 'wood' | 'fire' | 'earth' | 'metal' | 'water' | string;

interface ElementalParticlesProps {
    element: ElementType;
    isActive: boolean;
    intensity?: number;
}

const ElementalParticles = ({ element, isActive, intensity = 1 }: ElementalParticlesProps) => {
    if (!isActive) return null;

    // Configuration for each element
    const config = useMemo(() => {
        switch (element) {
            case 'fire':
                return {
                    count: 30,
                    colors: ['#ef4444', '#f59e0b', '#fbbf24', '#7f1d1d'], // Red, Amber, Yellow, Dark Red
                    direction: 'up',
                    speed: 2,
                    shape: 'circle',
                    blendMode: 'screen'
                };
            case 'water':
                return {
                    count: 25,
                    colors: ['#3b82f6', '#60a5fa', '#93c5fd', '#1e3a8a'], // Blue shades
                    direction: 'float',
                    speed: 1.5,
                    shape: 'circle',
                    blendMode: 'overlay'
                };
            case 'wood':
                return {
                    count: 20,
                    colors: ['#10b981', '#34d399', '#059669', '#064e3b'], // Emerald shades
                    direction: 'down',
                    speed: 1.5,
                    shape: 'leaf',
                    blendMode: 'normal'
                };
            case 'metal':
                return {
                    count: 25,
                    colors: ['#f8fafc', '#e2e8f0', '#94a3b8', '#ffffff'], // Slate/White
                    direction: 'sparkle',
                    speed: 0.5,
                    shape: 'star',
                    blendMode: 'overlay'
                };
            case 'earth':
                return {
                    count: 20,
                    colors: ['#d97706', '#b45309', '#fcd34d', '#78350f'], // Amber/Brown
                    direction: 'up-slow',
                    speed: 1,
                    shape: 'square',
                    blendMode: 'normal'
                };
            default:
                return {
                    count: 20,
                    colors: ['#ffffff'],
                    direction: 'float',
                    speed: 1,
                    shape: 'circle',
                    blendMode: 'screen'
                };
        }
    }, [element]);

    return (
        <div className="absolute inset-0 pointer-events-none overflow-visible z-0">
            {[...Array(Math.floor(config.count * intensity))].map((_, i) => (
                <Particle
                    key={i}
                    config={config}
                    index={i}
                />
            ))}
        </div>
    );
};

const Particle = ({ config, index }: { config: any, index: number }) => {
    // Randomize initial positions and animations based on config
    const randomX = Math.random() * 100; // Percentage
    const randomDelay = Math.random() * 0.5;
    const randomDuration = 1 + Math.random() * 1.5;
    const size = 4 + Math.random() * 8;

    // Animation Variants
    const variants = {
        up: {
            y: [100, -200], // Start below, move way up
            x: [0, (Math.random() - 0.5) * 50], // Drift
            opacity: [0, 1, 0],
            scale: [0.5, 1.5, 0]
        },
        'up-slow': {
            y: [50, -100],
            opacity: [0, 0.8, 0],
            rotate: [0, 90],
            scale: [0.8, 1.2, 0.8]
        },
        down: {
            y: [-50, 200], // Start above, fall down
            x: [0, (Math.random() - 0.5) * 100], // Sway
            rotate: [0, 360],
            opacity: [0, 1, 0]
        },
        float: {
            y: [50, -150],
            x: [(Math.random() - 0.5) * 20, (Math.random() - 0.5) * -20],
            scale: [0.8, 1.2, 0.8],
            opacity: [0, 0.6, 0]
        },
        sparkle: {
            scale: [0, 1, 0],
            rotate: [0, 180],
            opacity: [0, 1, 0],
            filter: ["brightness(1)", "brightness(2)", "brightness(1)"]
        }
    };

    const style: any = {
        top: config.direction === 'down' ? '-10%' : undefined,
        bottom: config.direction !== 'down' ? '-10%' : undefined,
        left: `${randomX}%`,
        width: size,
        height: size,
        backgroundColor: config.colors[index % config.colors.length],
        position: 'absolute',
        borderRadius: config.shape === 'circle' ? '50%' : config.shape === 'leaf' ? '0% 50% 50% 50%' : '2px',
        mixBlendMode: config.blendMode
    };

    // Special shapes (clip-path for star)
    if (config.shape === 'star') {
        style.clipPath = "polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)";
        style.backgroundColor = config.colors[Math.floor(Math.random() * config.colors.length)];
    }

    // Leaf rotation (initial)
    if (config.shape === 'leaf') {
        style.transform = `rotate(${Math.random() * 360}deg)`;
    }

    // Metal specific positioning (random all over)
    if (config.direction === 'sparkle') {
        style.top = `${Math.random() * 100}%`;
        style.bottom = undefined;
    }

    return (
        <motion.div
            style={style}
            animate={variants[config.direction as keyof typeof variants]}
            transition={{
                duration: randomDuration / config.speed,
                delay: randomDelay,
                repeat: Infinity,
                ease: config.direction === 'sparkle' ? "easeInOut" : "easeOut"
            }}
        />
    );
};

export default ElementalParticles;
