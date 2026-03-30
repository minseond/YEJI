import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Sparkles, ArrowLeft, X } from 'lucide-react';
import { useSound } from '../../hooks/useSound';

interface TarotStepResultProps {
    card: {
        name: string;
        img: string;
        type: string;
        desc: string;
        detailedDesc: string;
        keywords: string[];
        isReversed: boolean;
    };
    onNext: () => void;
    onBack: () => void;
    onExit: () => void;
}

const TarotStepResult: React.FC<TarotStepResultProps> = ({ card, onNext, onBack, onExit }) => {
    const { play } = useSound();

    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space') {
                e.preventDefault();
                play('SFX', 'CARD_FLIP');
                onNext();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onNext, play]);

    const handleNextClick = () => {
        play('SFX', 'CARD_FLIP');
        onNext();
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[60] flex flex-col items-center justify-center p-6 bg-[#020617] overflow-hidden"
        >
            {/* Background Atmosphere (Mystical Galaxy Theme) */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(88,28,135,0.15),transparent_70%)] pointer-events-none" />
            <div className="absolute top-0 left-0 w-full h-full opacity-[0.05] pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />

            {/* Magic Circle Background */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-10">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                    className="w-[800px] h-[800px] border border-purple-500/20 rounded-full border-dashed"
                />
            </div>

            {/* Top Navigation */}
            <div className="absolute top-8 left-8 right-8 z-[70] flex justify-between items-center pointer-events-none">
                <motion.button
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={onBack}
                    className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-slate-900/60 border border-purple-500/30 text-purple-100 shadow-xl hover:bg-slate-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm group"
                >
                    <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                    뒤로가기
                </motion.button>

                <motion.button
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={onExit}
                    className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-slate-900/60 border border-purple-500/30 text-purple-100 shadow-xl hover:bg-slate-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm group"
                >
                    나가기
                    <X size={20} className="group-hover:rotate-90 transition-transform" />
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
                    <div className="absolute -inset-10 bg-purple-600/20 blur-[60px] rounded-full animate-pulse-slow" />

                    <div className="relative w-64 h-96 md:w-80 md:h-[480px] bg-white/5 backdrop-blur-3xl border border-white/10 rounded-[2rem] overflow-hidden shadow-[0_40px_100px_rgba(0,0,0,0.8),inset_0_0_20px_rgba(168,85,247,0.1)] flex items-center justify-center group/card">
                        {/* Image */}
                        <img
                            src={card.img}
                            alt={card.name}
                            className={`w-full h-full object-cover scale-[1.15] transition-transform duration-700 ${card.isReversed ? 'rotate-180' : ''}`}
                        />

                        {/* Glass Shine Effect */}
                        <motion.div
                            className="absolute inset-0 bg-gradient-to-tr from-transparent via-purple-300/10 to-transparent -translate-x-full"
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
                        <div className="absolute inset-0 bg-gradient-to-t from-[#020617]/80 via-transparent to-white/5 pointer-events-none" />
                    </div>

                    {/* Step Label: Glass style */}
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 px-8 py-2.5 bg-black/40 backdrop-blur-xl border border-purple-500/40 rounded-full text-purple-200 text-[11px] tracking-[0.4em] font-black uppercase whitespace-nowrap shadow-xl">
                        {card.type}
                    </div>
                </motion.div>

                {/* Right: Interpretation Panel with Glass Design */}
                <div className="flex-1 flex flex-col gap-6 text-center md:text-left max-w-2xl bg-white/[0.02] backdrop-blur-md border border-white/[0.05] p-8 md:p-12 rounded-[3rem] shadow-2xl overflow-hidden relative group">
                    {/* Panel Inner Glow */}
                    <div className="absolute -top-20 -right-20 w-40 h-40 bg-purple-500/10 blur-[80px] group-hover:bg-purple-500/20 transition-all duration-1000" />

                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 }}
                        className="relative z-10"
                    >
                        <h2 className="text-purple-400 font-['Hahmlet'] text-xl tracking-[0.3em] mb-3 flex items-center justify-center md:justify-start gap-3">
                            <Sparkles size={20} className="text-purple-300" />
                            {card.name}
                            <span className="text-sm opacity-60 tracking-normal ml-2">({card.isReversed ? '역방향' : '정방향'})</span>
                        </h2>

                        <h1 className="text-3xl md:text-5xl font-bold font-['Hahmlet'] text-white/95 leading-tight mb-6">
                            {card.desc}
                        </h1>

                        <div className="flex justify-center md:justify-start mb-6">
                            <div className="h-[1px] w-32 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent md:from-purple-500/50 md:to-transparent" />
                        </div>

                        {/* Keywords */}
                        <div className="flex flex-wrap justify-center md:justify-start gap-2 mb-6">
                            {card.keywords.map((keyword, i) => (
                                <span key={i} className="px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-xs text-purple-200 font-bold">
                                    #{keyword}
                                </span>
                            ))}
                        </div>

                        <p className="text-white/70 font-serif text-lg leading-relaxed break-keep">
                            {card.detailedDesc}
                        </p>
                    </motion.div>

                    <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1.5 }}
                        onClick={handleNextClick}
                        className="relative z-10 self-center md:self-start flex items-center gap-4 px-10 py-4 mt-4 bg-purple-500/10 hover:bg-purple-500/20 backdrop-blur-xl border border-purple-500/20 hover:border-purple-500/50 rounded-full text-purple-100 font-bold transition-all duration-300 group overflow-hidden"
                    >
                        {/* Button Glow Effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />

                        <span className="tracking-widest font-['Hahmlet']">다음 카드</span>
                        <ChevronRight className="group-hover:translate-x-1 transition-transform text-purple-400" />
                    </motion.button>
                </div>
            </div>
        </motion.div>
    );
};

export default TarotStepResult;
