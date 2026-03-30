import { useState, useEffect, forwardRef } from 'react';
import { motion } from 'framer-motion';

interface AnimatedBubbleProps {
    text: string;
    theme?: 'indigo' | 'amber' | 'stone';
    size?: 'small' | 'normal' | 'large' | 'extra-large'; // Added small variant
    title?: string;
    className?: string;
}

const AnimatedBubble = forwardRef<HTMLDivElement, AnimatedBubbleProps>(({ text, theme = 'indigo', size = 'normal', title = 'INFO', className = '' }, ref) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isTyping, setIsTyping] = useState(true);

    useEffect(() => {
        setDisplayedText('');
        setIsTyping(true);
        let i = 0;
        const interval = setInterval(() => {
            if (i < text.length) {
                setDisplayedText(text.substring(0, i + 1));
                i++;
            } else {
                clearInterval(interval);
                setIsTyping(false);
            }
        }, 30); // Speed: 30ms per char
        return () => clearInterval(interval);
    }, [text]);

    const isIndigo = theme === 'indigo';
    const isAmber = theme === 'amber';

    // Theme configurations
    const themeConfig = {
        indigo: {
            bg: 'from-slate-900/95 to-slate-800/95',
            border: 'border-indigo-500/30',
            text: 'text-indigo-100 font-western',
            titleColor: 'text-indigo-400 font-western',
            titleBg: 'bg-indigo-900/50',
            dashes: 'bg-indigo-500/30',
            decor: 'bg-slate-800',
            caret: 'bg-indigo-500'
        },
        amber: {
            bg: 'bg-[#f4efe4]/95',
            border: 'border-stone-800/20',
            text: 'text-stone-900 font-eastern',
            titleColor: 'text-stone-800 font-eastern',
            titleBg: 'bg-stone-800/10',
            dashes: 'from-stone-800/20',
            decor: 'bg-[#f4efe4]',
            caret: 'bg-stone-800'
        },
        stone: { // Neutral/White theme for general use
            bg: 'from-zinc-900/95 to-zinc-800/95',
            border: 'border-white/20',
            text: 'text-white font-eastern',
            titleColor: 'text-white/80 font-eastern',
            titleBg: 'bg-white/10',
            dashes: 'bg-white/20',
            decor: 'bg-zinc-800',
            caret: 'bg-white'
        }
    };

    const currentTheme = isIndigo ? themeConfig.indigo : (isAmber ? themeConfig.amber : themeConfig.stone);

    // Size configurations
    const containerClasses = {
        small: `w-fit min-w-[15rem] max-w-sm p-4`,
        normal: `w-fit min-w-[20rem] max-w-2xl p-5`,
        large: `w-fit min-w-[26rem] max-w-3xl p-6`,
        'extra-large': `w-fit min-w-[32rem] max-w-[55rem] max-w-[95vw] p-7`
    }[size];

    const textClasses = {
        small: `text-xs md:text-sm min-h-[2rem] break-keep`,
        normal: `text-sm md:text-base min-h-[2.5rem] break-keep`,
        large: `text-lg md:text-xl min-h-[3.5rem] break-keep`,
        'extra-large': `text-lg md:text-xl min-h-[3.5rem] break-keep`
    }[size];

    return (
        <motion.div
            ref={ref}
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            className={`absolute bg-gradient-to-br ${currentTheme.bg} ${containerClasses} rounded-tr-3xl rounded-bl-3xl rounded-tl-lg rounded-br-lg border ${currentTheme.border} shadow-2xl z-20 text-left whitespace-pre-wrap ${className}`}
        >

            <div className="mb-3 flex items-center gap-2">
                <span className={`px-2 py-0.5 ${currentTheme.titleBg} border ${currentTheme.border} rounded-full ${currentTheme.titleColor} text-xs font-bold tracking-widest uppercase`}>
                    {title}
                </span>
                <div className={`h-[1px] flex-1 bg-gradient-to-r ${currentTheme.dashes} to-transparent`} />
            </div>

            <p className={`${currentTheme.text} leading-relaxed ${textClasses} relative`}>
                {displayedText}
                {isTyping ? (
                    <span className={`inline-block w-1.5 h-4 ml-1 mb-[-2px] animate-pulse ${currentTheme.caret}`} />
                ) : (
                    <span className="absolute bottom-[-10px] right-0 animate-bounce text-sm opacity-70">
                        ▼
                    </span>
                )}
            </p>
        </motion.div>
    );
});

export default AnimatedBubble;
