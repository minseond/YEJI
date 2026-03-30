import { motion } from 'framer-motion';
import { ChevronRight } from 'lucide-react';

interface TarotCardRevealProps {
    stepTitle: string;      // e.g., "과거", "현재", "미래"
    cardName: string;       // e.g., "The Fool", "The Magician"
    cardDescription: string; // Card interpretation text
    cardImageUrl?: string;  // Optional card image (for future)
    isReversed: boolean;    // Whether card is upside-down
    onNext: () => void;
}

const TarotCardReveal = ({
    stepTitle,
    cardName,
    cardDescription,
    cardImageUrl,
    isReversed,
    onNext
}: TarotCardRevealProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 flex items-center justify-center p-4 md:p-8 overflow-y-auto"
        >
            {/* Main Container - Responsive Grid */}
            <div className="w-full max-w-6xl my-auto">
                {/* Step Title */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-center mb-6 md:mb-8"
                >
                    <h3 className="text-xl md:text-3xl font-['GmarketSansBold'] text-purple-300/60 tracking-[0.3em]">
                        {stepTitle}
                    </h3>
                </motion.div>

                {/* Content Grid: Vertical on mobile, Horizontal on desktop */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-12 items-center">
                    {/* Left: Card Display */}
                    <motion.div
                        initial={{ opacity: 0, x: -50, rotateY: -90 }}
                        animate={{ opacity: 1, x: 0, rotateY: 0 }}
                        transition={{
                            delay: 0.4,
                            type: "spring",
                            stiffness: 100,
                            damping: 15
                        }}
                        className="flex flex-col items-center"
                    >
                        {/* Card Image / Placeholder */}
                        <div className="relative w-56 h-80 md:w-72 md:h-96 lg:w-80 lg:h-[480px] bg-gradient-to-br from-purple-900/40 to-purple-950/60 rounded-2xl border-2 border-purple-500/30 shadow-2xl overflow-hidden backdrop-blur-sm">
                            {cardImageUrl ? (
                                <>
                                    <img
                                        src={cardImageUrl}
                                        alt={cardName}
                                        className="w-full h-full object-cover"
                                        style={{
                                            transform: isReversed ? 'rotate(180deg)' : 'rotate(0deg)'
                                        }}
                                    />

                                    {/* Reversed Indicator */}
                                    {isReversed && (
                                        <div className="absolute top-4 right-4 bg-red-600/90 text-white px-3 py-1.5 rounded-full text-xs font-bold backdrop-blur-sm shadow-lg z-10">
                                            역방향
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="absolute inset-0 flex flex-col items-center justify-center p-6">
                                    {/* Mystical Symbol Placeholder */}
                                    <motion.div
                                        animate={{
                                            rotate: 360,
                                            scale: [1, 1.1, 1]
                                        }}
                                        transition={{
                                            rotate: { duration: 20, repeat: Infinity, ease: "linear" },
                                            scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
                                        }}
                                        className="w-24 h-24 md:w-32 md:h-32 rounded-full border-2 border-dashed border-purple-400/50 mb-6"
                                    >
                                        <div className="w-full h-full flex items-center justify-center">
                                            <div className="w-12 h-12 md:w-16 md:h-16 bg-purple-500/20 rounded-full shadow-[0_0_30px_rgba(168,85,247,0.3)]" />
                                        </div>
                                    </motion.div>

                                    <h4 className="text-2xl md:text-3xl font-['Cinzel'] text-purple-100 text-center tracking-wider">
                                        {cardName}
                                    </h4>

                                    {/* Reversed Indicator for Placeholder */}
                                    {isReversed && (
                                        <div className="mt-4 bg-red-600/20 text-red-300 px-4 py-2 rounded-full text-sm font-bold border border-red-500/30">
                                            역방향
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Glow Effect */}
                            <div className="absolute inset-0 bg-gradient-radial from-purple-500/20 via-transparent to-transparent opacity-50 pointer-events-none" />
                        </div>

                        {/* Card Name (if image is shown) */}
                        {cardImageUrl && (
                            <motion.h4
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.8 }}
                                className="text-center mt-4 md:mt-6 text-2xl md:text-3xl font-['Cinzel'] text-purple-100 tracking-wider"
                            >
                                {cardName}
                            </motion.h4>
                        )}
                    </motion.div>

                    {/* Right: Interpretation & Button */}
                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.6 }}
                        className="flex flex-col gap-6 lg:gap-8 max-h-[60vh] lg:max-h-[70vh]"
                    >
                        {/* Card Interpretation - Scrollable */}
                        <div className="bg-purple-950/30 backdrop-blur-md rounded-2xl p-6 md:p-8 border border-purple-500/20 shadow-lg overflow-y-auto max-h-[40vh] lg:max-h-[55vh]">
                            <p className="text-purple-50/90 text-base md:text-lg leading-relaxed font-['Pretendard'] whitespace-pre-line">
                                {cardDescription}
                            </p>
                        </div>

                        {/* Next Button */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.8 }}
                            className="flex justify-center lg:justify-start"
                        >
                            <motion.button
                                whileHover={{ scale: 1.05, x: 5 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onNext}
                                className="group px-8 md:px-10 py-3 md:py-4 bg-gradient-to-r from-purple-600 to-purple-700 rounded-xl font-['GmarketSansBold'] text-base md:text-lg text-white shadow-lg hover:shadow-purple-500/50 transition-all flex items-center gap-3"
                            >
                                다음
                                <ChevronRight
                                    className="w-5 h-5 transition-transform group-hover:translate-x-1"
                                />
                            </motion.button>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </motion.div>
    );
};

export default TarotCardReveal;
