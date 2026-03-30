import React from 'react';
import { motion } from 'framer-motion';

const InkBackground: React.FC = () => {
    return (
        <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10 bg-[#0b0d14]">
            {/* Deep Base Gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#1F1F33] via-[#0F1016] to-[#000000] opacity-90" />

            {/* Moving Fog / Ink Layers */}
            {/* Layer 1: Slow, Deep Fog */}
            <motion.div
                animate={{
                    x: ["-10%", "10%"],
                    y: ["-5%", "5%"],
                }}
                transition={{
                    duration: 20,
                    repeat: Infinity,
                    repeatType: "reverse",
                    ease: "easeInOut"
                }}
                className="absolute inset-0 opacity-50 mix-blend-screen"
                style={{
                    backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(74, 108, 111, 0.3), transparent 60%)',
                    filter: 'blur(60px)',
                    transform: 'scale(1.2)'
                }}
            />

            {/* Layer 2: Drifting Clouds (Textured) */}
            <motion.div
                animate={{
                    x: ["0%", "-5%"],
                    y: ["0%", "-2%"],
                }}
                transition={{
                    duration: 15,
                    repeat: Infinity,
                    repeatType: "reverse",
                    ease: "easeInOut"
                }}
                className="absolute inset-0 opacity-30 bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')] mix-blend-overlay"
            />

            {/* Layer 3: Floating Ink Spots */}
            <motion.div
                animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.3, 0.5, 0.3],
                }}
                transition={{
                    duration: 8,
                    repeat: Infinity,
                    repeatType: "reverse",
                    ease: "easeInOut"
                }}
                className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-gradient-to-r from-[#D4AF37]/20 to-transparent blur-[80px]"
            />
            <motion.div
                animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.2, 0.4, 0.2],
                }}
                transition={{
                    duration: 12,
                    repeat: Infinity,
                    repeatType: "reverse",
                    ease: "easeInOut",
                    delay: 2
                }}
                className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] rounded-full bg-gradient-to-l from-[#4A6C6F]/30 to-transparent blur-[100px]"
            />

            {/* Dynamic Accent Lights - Moonlight effect */}
            <motion.div
                animate={{
                    opacity: [0.1, 0.4, 0.1],
                    scale: [0.8, 1, 0.8],
                }}
                transition={{
                    duration: 10,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
                className="absolute top-0 right-0 w-[800px] h-[800px] bg-[#D4AF37]/10 rounded-full blur-[150px]"
            />

        </div>
    );
};

export default InkBackground;
