import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

interface FlipCardProps {
    frontImage: string;
    backImage: string;
    isRevealed: boolean;
    width?: string | number;
    height?: string | number;
    className?: string;
    onRevealComplete?: () => void;
}

const FlipCard = ({
    frontImage,
    backImage,
    isRevealed,
    width = 300,
    height = 480,
    className = "",
    onRevealComplete
}: FlipCardProps) => {
    const [isFlipped, setIsFlipped] = useState(false);

    useEffect(() => {
        if (isRevealed) {
            setIsFlipped(true);
            // Notify completion generally after animation
            const timer = setTimeout(() => {
                onRevealComplete?.();
            }, 1000); // slightly longer than duration
            return () => clearTimeout(timer);
        }
    }, [isRevealed, onRevealComplete]);

    return (
        <div className={`relative perspective-1000 ${className}`} style={{ width, height }}>
            <motion.div
                className="w-full h-full relative preserve-3d"
                initial={{ rotateY: 0 }}
                animate={{ rotateY: isFlipped ? 180 : 0 }}
                transition={{ duration: 0.8, type: "spring", stiffness: 60, damping: 12 }}
                style={{ transformStyle: "preserve-3d" }}
            >
                {/* Back of Card (Initially Visible) */}
                <div
                    className="absolute inset-0 w-full h-full backface-hidden rounded-xl shadow-2xl overflow-hidden border-2 border-white/10"
                    style={{
                        backfaceVisibility: "hidden",
                        backgroundImage: `url(${backImage})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                    }}
                >
                    {/* Glossy Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
                </div>

                {/* Front of Card (Revealed on Flip) */}
                <div
                    className="absolute inset-0 w-full h-full backface-hidden rounded-xl shadow-2xl overflow-hidden"
                    style={{
                        backfaceVisibility: "hidden",
                        transform: "rotateY(180deg)",
                        backgroundImage: `url(${frontImage})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                    }}
                >
                    {/* Inner Shadow for Depth */}
                    <div className="absolute inset-0 ring-1 ring-black/10 rounded-xl pointer-events-none" />
                </div>
            </motion.div>
        </div>
    );
};

export default FlipCard;
