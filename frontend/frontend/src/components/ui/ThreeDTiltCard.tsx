import { motion, useMotionTemplate, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { type MouseEvent, type ReactNode, useRef } from 'react';

interface ThreeDTiltCardProps {
    children: ReactNode;
    className?: string;
    glowColor?: string;
}

const ThreeDTiltCard = ({ children, className = "", glowColor = "rgba(255,255,255,0.2)" }: ThreeDTiltCardProps) => {
    const ref = useRef<HTMLDivElement>(null);

    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["5deg", "-5deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-5deg", "5deg"]);

    const background = useMotionTemplate`radial-gradient(
        800px circle at ${mouseX}px ${mouseY}px,
        ${glowColor},
        transparent 40%
    )`;

    const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;

        const rect = ref.current.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;

        const mouseXPos = e.clientX - rect.left;
        const mouseYPos = e.clientY - rect.top;

        const xPct = mouseXPos / width - 0.5;
        const yPct = mouseYPos / height - 0.5;

        x.set(xPct);
        y.set(yPct);
    };

    const handleMouseLeave = () => {
        x.set(0);
        y.set(0);
    };

    return (
        <motion.div
            ref={ref}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            style={{
                rotateX,
                rotateY,
                transformStyle: "preserve-3d",
            }}
            className={`relative transition-all duration-200 ease-out ${className}`}
        >
            <div
                style={{
                    transform: "translateZ(75px)",
                    transformStyle: "preserve-3d",
                }}
                className="absolute inset-4 rounded-[2rem] shadow-lg pointer-events-none border border-white/5" // Inner frame depth
            />
            {/* Reflection Gradient */}
            <motion.div
                className="absolute inset-0 z-50 rounded-3xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                style={{
                    background
                }}
            />
            {children}
        </motion.div>
    );
};

export default ThreeDTiltCard;
