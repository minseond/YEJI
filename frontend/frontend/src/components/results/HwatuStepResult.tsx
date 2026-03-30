import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, ChevronLeft, Sparkles, X } from 'lucide-react';
import { useSound } from '../../hooks/useSound';

interface HwatuStepResultProps {
    card: {
        name: string;
        img: string;
        type: string;
        desc: string;
        detailedDesc: string;
    };
    onNext: () => void;
    onPrev?: () => void;
    isFirstStep?: boolean;
    isLastStep?: boolean;
    onExit: () => void;
}

const HwatuStepResult: React.FC<HwatuStepResultProps> = ({ card, onNext, onPrev, isFirstStep, isLastStep, onExit }) => {
    const { play } = useSound();

    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.code === 'ArrowRight') {
                e.preventDefault();
                play('SFX', 'CARD_FLIP');
                onNext();
            } else if ((e.code === 'ArrowLeft') && onPrev && !isFirstStep) {
                e.preventDefault();
                play('SFX', 'CARD_FLIP');
                onPrev();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onNext, onPrev, isFirstStep, play]);

    const handleNextClick = () => {
        play('SFX', 'CARD_FLIP');
        onNext();
    };

    const handlePrevClick = () => {
        if (onPrev && !isFirstStep) {
            play('SFX', 'CARD_FLIP');
            onPrev();
        }
    };
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[60] bg-[#0c0a09] overflow-hidden"
        >
            <div className="h-full w-full flex flex-col items-center justify-center p-6 md:p-12 relative">
                {/* Background Atmosphere */}
                <div className="fixed inset-0 bg-[radial-gradient(circle_at_center,rgba(159,18,57,0.15),transparent_70%)] pointer-events-none" />
                <div className="fixed top-0 left-0 w-full h-full opacity-[0.03] pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />

                {/* Top Navigation */}
                <div className="fixed top-8 left-8 right-8 z-[100] flex justify-end items-center pointer-events-none">


                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        onClick={onExit}
                        className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-stone-900/60 border border-amber-900/40 text-amber-100 shadow-xl hover:bg-stone-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                    >
                        나가기
                        <X size={20} />
                    </motion.button>
                </div>

                <div className="relative z-10 w-full max-w-6xl flex flex-col md:flex-row items-center justify-center gap-12 md:gap-20">
                    {/* Left: Card Reveal with Glass Frame */}
                    <motion.div
                        initial={{ scale: 0.8, rotateY: 180, opacity: 0 }}
                        animate={{ scale: 1, rotateY: 0, opacity: 1 }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="relative shrink-0"
                    >
                        {/* Glow effect behind the card */}
                        <div className="absolute -inset-10 bg-amber-600/20 blur-[60px] rounded-full animate-pulse-slow" />

                        <div className="relative w-64 h-96 md:w-80 md:h-[480px] bg-red-950/40 backdrop-blur-3xl border-8 border-double border-amber-900/60 rounded-[2rem] overflow-hidden shadow-[0_40px_100px_rgba(0,0,0,0.8),inset_0_0_40px_rgba(0,0,0,0.5)] flex items-center justify-center group/card">
                            {/* Oriental Pattern Border Overlay */}
                            <div className="absolute inset-0 border border-amber-500/20 rounded-[1.5rem] pointer-events-none z-10" />

                            {/* Image: Fills the container, but with background padding if needed */}
                            <img
                                src={card.img}
                                alt={card.name}
                                className="w-full h-full object-contain md:object-cover transition-transform duration-700 bg-red-950 scale-x-[1.03]"
                            />

                            {/* Glass Shine Effect */}
                            <motion.div
                                className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent -translate-x-full"
                                animate={{
                                    x: ['-100%', '200%'],
                                }}
                                transition={{
                                    duration: 2.5,
                                    repeat: Infinity,
                                    ease: "easeInOut",
                                    repeatDelay: 1
                                }}
                            />

                            {/* Inner Glass Shadow Overlay */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-white/10 pointer-events-none" />
                        </div>

                        {/* Step Label: Glass style - Moved to Bottom and Enlarged */}
                        <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 px-10 py-3 bg-black/60 backdrop-blur-2xl border-2 border-amber-500/40 rounded-full text-amber-200 text-sm md:text-base tracking-[0.5em] font-bold uppercase whitespace-nowrap shadow-[0_10px_30px_rgba(0,0,0,0.5)] z-20">
                            {card.type}
                        </div>
                    </motion.div>

                    {/* Right: Interpretation Panel with Glass Design */}
                    <div className="flex-1 w-full max-w-2xl h-[500px] md:h-[600px] flex flex-col bg-white/[0.02] backdrop-blur-md border border-white/[0.05] rounded-[3rem] shadow-2xl overflow-hidden relative group">
                        {/* Panel Inner Glow */}
                        <div className="absolute -top-20 -right-20 w-40 h-40 bg-amber-500/10 blur-[80px] group-hover:bg-amber-500/20 transition-all duration-1000" />

                        <div
                            className="flex-1 overflow-y-auto custom-scrollbar p-8 md:p-12 relative"
                        >
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.5 }}
                                className="relative z-10"
                            >
                                <h2 className="text-amber-500 font-['Hahmlet'] text-xl tracking-[0.3em] mb-3 flex items-center justify-center md:justify-start gap-3">
                                    <Sparkles size={20} className="text-amber-400" /> {card.name}
                                </h2>
                                <h1 className={`font-bold font-['Hahmlet'] text-white/95 leading-tight mb-8 break-keep transition-all duration-500 ${card.desc.length > 25 ? 'text-2xl md:text-3xl' :
                                    card.desc.length > 15 ? 'text-3xl md:text-5xl' :
                                        'text-4xl md:text-6xl'
                                    }`}>
                                    {card.desc}
                                </h1>

                                <div className="flex justify-center md:justify-start mb-8">
                                    <div className="h-[1px] w-32 bg-gradient-to-r from-transparent via-amber-500/50 to-transparent md:from-amber-500/50 md:to-transparent" />
                                </div>

                                <div className="text-white/70 font-['Hahmlet'] text-lg md:text-2xl leading-relaxed break-keep space-y-4">
                                    {card.detailedDesc.split(/(?<=[.!?])\s+/).map((sentence, sIdx) => (
                                        <p key={sIdx}>{sentence}</p>
                                    ))}
                                </div>
                            </motion.div>
                        </div>

                        <div className="flex-shrink-0 p-8 md:p-12 pt-0 flex flex-col sm:flex-row items-center justify-center md:justify-start gap-4 relative z-10 bg-gradient-to-t from-black/20 to-transparent">
                            {onPrev && !isFirstStep && (
                                <motion.button
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 1.4 }}
                                    onClick={handlePrevClick}
                                    className="w-full sm:w-40 flex items-center justify-center gap-3 px-6 py-4 bg-white/5 hover:bg-white/10 backdrop-blur-xl border border-white/10 hover:border-amber-500/50 rounded-full text-amber-100/60 hover:text-amber-100 transition-all duration-300 group"
                                >
                                    <ChevronLeft size={18} className="group-hover:-translate-x-1 transition-transform text-amber-700" />
                                    <span className="tracking-widest font-['Hahmlet'] text-sm">이전 카드</span>
                                </motion.button>
                            )}

                            <motion.button
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 1.5 }}
                                onClick={handleNextClick}
                                className="w-full sm:min-w-[170px] sm:w-auto flex items-center justify-center gap-2 px-6 py-4 bg-white/5 hover:bg-white/10 backdrop-blur-xl border border-white/10 hover:border-amber-500/50 rounded-full text-amber-100 font-bold transition-all duration-300 group overflow-hidden"
                            >
                                {/* Button Glow Effect */}
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-500/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />

                                <span className="tracking-widest font-['Hahmlet'] text-sm whitespace-nowrap">
                                    {isLastStep ? '보고서 보기' : '다음 카드'}
                                </span>
                                <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform text-amber-500 shrink-0" />
                            </motion.button>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default HwatuStepResult;
