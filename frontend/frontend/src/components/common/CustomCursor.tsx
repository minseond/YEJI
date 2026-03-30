import { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

export default function CustomCursor() {
    const [isPointer, setIsPointer] = useState(false);
    const [isClicking, setIsClicking] = useState(false);

    // Mouse position
    const mouseX = useMotionValue(-100);
    const mouseY = useMotionValue(-100);

    // Smooth spring animation for the trailing cursor
    const springConfig = { damping: 25, stiffness: 200, mass: 0.5 };
    const cursorX = useSpring(mouseX, springConfig);
    const cursorY = useSpring(mouseY, springConfig);

    useEffect(() => {
        const moveCursor = (e: MouseEvent) => {
            mouseX.set(e.clientX);
            mouseY.set(e.clientY);

            // Check if hovering over clickable element
            const target = e.target as HTMLElement;
            const isClickable =
                target.tagName === 'BUTTON' ||
                target.tagName === 'A' ||
                target.closest('button') ||
                target.closest('a') ||
                target.dataset.cursor === 'pointer' ||
                target.style.cursor === 'pointer';

            setIsPointer(!!isClickable);
        };

        const handleMouseDown = () => setIsClicking(true);
        const handleMouseUp = () => setIsClicking(false);

        window.addEventListener('mousemove', moveCursor);
        window.addEventListener('mousedown', handleMouseDown);
        window.addEventListener('mouseup', handleMouseUp);

        return () => {
            window.removeEventListener('mousemove', moveCursor);
            window.removeEventListener('mousedown', handleMouseDown);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [mouseX, mouseY]);

    return (
        <>
            {/* Main Dot Cursor (Fixed position, immediate) */}
            <motion.div
                className="fixed top-0 left-0 w-2 h-2 bg-white rounded-full pointer-events-none z-[9999999] mix-blend-difference"
                style={{
                    x: mouseX,
                    y: mouseY,
                    translateX: '-50%',
                    translateY: '-50%',
                }}
            />

            {/* Trailing Glow Cursor (Smooth spring) */}
            <motion.div
                className="fixed top-0 left-0 pointer-events-none z-[9999998]"
                style={{
                    x: cursorX,
                    y: cursorY,
                    translateX: '-50%',
                    translateY: '-50%',
                }}
                animate={{
                    width: isPointer ? 64 : 32,
                    height: isPointer ? 64 : 32,
                    opacity: isClicking ? 0.8 : isPointer ? 0.5 : 0.3,
                    scale: isClicking ? 0.8 : 1,
                }}
                transition={{
                    type: "spring",
                    stiffness: 300,
                    damping: 20
                }}
            >
                {/* Glow Effect */}
                <div className={`w-full h-full rounded-full transition-colors duration-300 ${isClicking ? 'bg-red-400 blur-md' : 'bg-purple-400 blur-xl'}`} />

                {/* Inner Ring (Visible on hover) */}
                {isPointer && (
                    <div className="absolute inset-0 border border-white/50 rounded-full animate-ping-slow" />
                )}
            </motion.div>
        </>
    );
}
