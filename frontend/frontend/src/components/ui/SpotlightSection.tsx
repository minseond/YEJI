import { motion } from 'framer-motion';
import { type ReactNode, useEffect, useRef } from 'react';

interface SpotlightSectionProps {
    children: ReactNode;
    isActive: boolean;
    isDimmed: boolean; // True if ANOTHER section is active
    className?: string;
    onActivate?: () => void;
}

const SpotlightSection = ({ children, isActive, isDimmed, className = "", onActivate }: SpotlightSectionProps) => {
    const ref = useRef<HTMLDivElement>(null);

    // Auto-scroll when active
    useEffect(() => {
        if (isActive && ref.current) {
            ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
            if (onActivate) onActivate();
        }
    }, [isActive, onActivate]);

    return (
        <motion.div
            ref={ref}
            animate={{
                opacity: isDimmed ? 0.2 : 1,
                scale: isActive ? 1.02 : 1,
                filter: isDimmed ? 'blur(2px)' : 'none',
            }}
            transition={{ duration: 0.5 }}
            className={`relative transition-all duration-500 ${className} ${isActive ? 'z-40' : 'z-0'}`}
        >
            {/* Highlight Glow Border when Active */}
            {isActive && (
                <motion.div
                    layoutId="spotlight-glow"
                    className="absolute -inset-4 rounded-xl border-2 border-amber-500/50 bg-amber-500/5 shadow-[0_0_50px_rgba(245,158,11,0.2)] pointer-events-none z-0"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                />
            )}
            <div className="relative z-10">
                {children}
            </div>
        </motion.div>
    );
};

export default SpotlightSection;
