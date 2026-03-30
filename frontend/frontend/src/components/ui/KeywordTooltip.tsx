import { motion } from 'framer-motion';
import { useState } from 'react';

interface KeywordTooltipProps {
    keyword: string;
    description: string;
    themeColor: string; // e.g., "text-amber-500" or hex
    borderColor: string;
    bgColor: string;
}

const KeywordTooltip = ({ keyword, description, themeColor, borderColor, bgColor }: KeywordTooltipProps) => {
    const [isHovered, setIsHovered] = useState(false);

    return (
        <div className="relative inline-block margin-1">
            <motion.div
                onHoverStart={() => setIsHovered(true)}
                onHoverEnd={() => setIsHovered(false)}
                className={`px-3 py-1 rounded-full border ${borderColor} ${themeColor} text-sm ${bgColor} cursor-help relative z-10`}
                whileHover={{ scale: 1.1, y: -2 }}
                transition={{ type: "spring", stiffness: 300 }}
            >
                #{keyword}
            </motion.div>

            {/* Tooltip */}
            <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.8 }}
                animate={{
                    opacity: isHovered ? 1 : 0,
                    y: isHovered ? -40 : 10,
                    scale: isHovered ? 1 : 0.8,
                    pointerEvents: isHovered ? "auto" : "none"
                }}
                className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-max max-w-[200px] bg-black/90 border border-white/20 text-white text-xs p-2 rounded-lg backdrop-blur-md shadow-xl z-20 pointer-events-none"
            >
                {description}
                {/* Arrow */}
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-black/90" />
            </motion.div>
        </div>
    );
};

export default KeywordTooltip;
