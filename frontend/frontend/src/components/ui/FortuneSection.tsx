import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

interface FortuneSectionProps {
    title: string;
    content: string;
    score?: number;
    delay?: number;
    defaultExpanded?: boolean;
    themeColor?: string; // e.g. "text-amber-200"
}

const FortuneSection = ({
    title,
    content,
    score,
    delay = 0,
    defaultExpanded = true,
    themeColor = "text-amber-200"
}: FortuneSectionProps) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.5 }}
            className={`
                group relative pl-6 border-l border-white/10 hover:border-white/30 transition-all duration-300
                bg-gradient-to-r from-transparent via-transparent to-white/5 hover:to-white/10 rounded-r-xl
            `}
        >
            {/* Header / Click Area */}
            <div
                className="flex justify-between items-center mb-2 cursor-pointer py-2 pr-2"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <motion.div
                        animate={{ rotate: isExpanded ? 0 : -90 }}
                        className="text-white/40 group-hover:text-white transition-colors"
                    >
                        <ChevronDown size={18} />
                    </motion.div>
                    <h4 className={`text-lg font-bold text-white/90 group-hover:text-white transition-colors flex items-center gap-2`}>
                        {title}
                    </h4>
                </div>

                {score && (
                    <div className="flex items-center gap-2">
                        {/* Score Bar */}
                        <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden hidden sm:block">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${score}%` }}
                                transition={{ delay: delay + 0.5, duration: 1, ease: "easeOut" }}
                                className={`h-full ${score > 80 ? 'bg-amber-400' : score > 50 ? 'bg-blue-400' : 'bg-white/40'}`}
                            />
                        </div>
                        <span className="text-xs px-2 py-1 rounded bg-white/10 text-white/60 font-mono">
                            {score}
                        </span>
                    </div>
                )}
            </div>

            {/* Expandable Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                    >
                        <div className="pb-4 pr-4">
                            <p className="text-white/70 font-['Gowun_Batang'] leading-loose text-justify text-base">
                                {content}
                            </p>

                            {/* Decorative footer line */}
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: "100%" }}
                                transition={{ delay: 0.2, duration: 0.8 }}
                                className="h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent mt-4"
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Decorative Pulse (Active Element indicator) on the left border */}
            <motion.div
                className={`absolute left-[-1px] top-0 bottom-0 w-[2px] ${themeColor.replace('text-', 'bg-')}`}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: isExpanded ? 1 : 0 }}
                transition={{ duration: 0.3 }}
            />
        </motion.div>
    );
};

export default FortuneSection;
