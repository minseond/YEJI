import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Quote, ArrowLeft, X } from 'lucide-react';
import { useCharacterSettings } from '../../utils/character';

interface HwatuStoryResultProps {
    data: {
        cards: Array<{
            name: string;
            img: string;
            type: string;
            desc: string;
            detailedDesc: string;
        }>;
        summary: {
            keyword: string;
            summary: string;
            report: string;
            lucky?: { color: string; number: string; direction: string; timing: string };
        };
    };
    onRestart: () => void;
    onExit: () => void;
    onBack: () => void;
}

const HwatuStoryResult: React.FC<HwatuStoryResultProps> = React.memo(({ data, onRestart, onExit, onBack }) => {
    const characterSettings = useCharacterSettings();
    const equippedEastId = characterSettings.east;
    const characterImage = `/assets/character/east/${equippedEastId}/${equippedEastId}_normal.png`;

    return (
        <div className="relative w-full h-full bg-black/40 overflow-hidden font-['Hahmlet']">
            <div className="h-full w-full flex flex-col items-center justify-center py-6 px-6 md:px-12 relative">
                {/* Top Navigation */}
                <div className="fixed top-8 left-8 right-8 z-[100] flex justify-between items-center pointer-events-none">
                    <motion.button
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        onClick={onBack}
                        className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-stone-900/60 border border-amber-900/40 text-amber-100 shadow-xl hover:bg-stone-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                    >
                        <ArrowLeft size={20} />
                        뒤로가기
                    </motion.button>

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

                {/* Background Effects */}
                <div className="absolute inset-0 pointer-events-none">
                    <motion.div
                        animate={{
                            opacity: [0.2, 0.4, 0.2],
                            scale: [1, 1.2, 1]
                        }}
                        transition={{ duration: 8, repeat: Infinity }}
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle,rgba(251,191,36,0.15)_0%,transparent_70%)] blur-[100px]"
                    />
                </div>

                <div className="relative z-10 w-full max-w-7xl h-full flex flex-col md:flex-row items-center justify-center gap-8 px-6 md:px-12">

                    {/* Character Side */}
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="relative w-full md:w-1/2 h-[40vh] md:h-[90vh] flex items-end justify-center z-10"
                    >
                        <motion.div
                            animate={{ y: [0, -15, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="relative w-full h-full flex items-end justify-center"
                        >
                            <img
                                src={characterImage}
                                alt="Master Character"
                                className="w-auto h-[90%] md:h-[95%] object-contain drop-shadow-[0_0_50px_rgba(251,191,36,0.3)] brightness-110"
                            />

                            {/* Golden Aura Ring */}
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                                className="absolute bottom-[20%] left-1/2 -translate-x-1/2 w-[120%] aspect-square border-2 border-dashed border-amber-500/10 rounded-full -z-10"
                            />
                        </motion.div>
                    </motion.div>

                    {/* Narrative Side */}
                    <div className="w-full md:w-1/2 flex flex-col justify-center items-center md:items-start gap-8 z-20">

                        {/* Hanji Speech Bubble */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 30 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.3 }}
                            className="relative w-full max-w-2xl h-[400px] md:h-[500px]"
                        >
                            {/* Speech Bubble Container */}
                            <div className="relative h-full p-8 md:p-12 bg-[#fdfcf5] text-stone-900 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.5),inset_0_0_100px_rgba(139,69,19,0.05)] border-4 border-double border-amber-900/30 overflow-hidden flex flex-col">

                                {/* Paper Texture Overlay */}
                                <div className="absolute inset-0 opacity-[0.08] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/rice-paper.png')]" />

                                {/* Decorative Corners */}
                                <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-amber-900/20" />
                                <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-amber-900/20" />
                                <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-amber-900/20" />
                                <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-amber-900/20" />

                                <Quote className="absolute top-6 left-6 text-amber-900/10 w-12 h-12" />

                                <div className="relative flex flex-col h-full space-y-6">
                                    <div className="space-y-2 flex-shrink-0">
                                        <motion.h3
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: 0.5 }}
                                            className="text-amber-700 text-sm tracking-[0.3em] font-medium"
                                        >
                                            오늘의 점괘 보고서
                                        </motion.h3>
                                        <motion.h2
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: 0.7 }}
                                            className="text-3xl md:text-4xl font-bold tracking-tight text-stone-800"
                                        >
                                            {data.summary.keyword}
                                        </motion.h2>
                                    </div>

                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.8, delay: 1 }}
                                        className="flex-1 overflow-y-auto custom-scrollbar text-lg md:text-xl leading-relaxed text-stone-700 font-medium whitespace-pre-line pr-2 relative"
                                    >
                                        {/* Swapped Advice and Flow Analysis */}
                                        {data.summary.report.includes('[조언]') ? (
                                            <>
                                                <span className="block text-amber-800 font-bold mb-1">[그대를 위한 조언]</span>
                                                <div className="space-y-4 mb-8">
                                                    {data.summary.report.split('[조언]')[1].trim().split(/(?<=[.!?])\s+/).map((s, i) => (
                                                        <p key={i}>{s}</p>
                                                    ))}
                                                </div>
                                                <div className="my-6 border-t border-amber-900/10" />
                                                <div className="space-y-4">
                                                    {data.summary.report.split('[조언]')[0].trim().split(/(?<=[.!?])\s+/).map((s, i) => (
                                                        <p key={i}>{s}</p>
                                                    ))}
                                                </div>
                                            </>
                                        ) : (
                                            <div className="space-y-4">
                                                {data.summary.report.split(/(?<=[.!?])\s+/).map((s, i) => (
                                                    <p key={i}>{s}</p>
                                                ))}
                                            </div>
                                        )}
                                    </motion.div>
                                </div>
                            </div>

                            {/* Speech Bubble Triangle */}
                            <div className="absolute top-1/2 -left-4 md:-left-6 -translate-y-1/2 w-8 md:w-12 h-8 md:h-12 bg-[#fdfcf5] border-l-4 border-b-4 border-double border-amber-900/30 rotate-45 -z-10 rounded-bl-lg hidden md:block" />
                        </motion.div>

                        {/* Buttons */}
                        <AnimatePresence>
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 1.5 }}
                                className="w-full flex justify-center md:justify-start"
                            >
                                <button
                                    onClick={onRestart}
                                    className="group px-12 py-5 bg-amber-900 text-amber-100 rounded-full font-bold flex items-center gap-3 hover:bg-amber-800 transition-all shadow-2xl hover:shadow-amber-900/40 border border-amber-500/20"
                                >
                                    <FileText className="w-6 h-6 group-hover:scale-110 transition-transform duration-300" />
                                    <span className="text-lg tracking-widest">최종 보고서 보기</span>
                                </button>
                            </motion.div>
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    );
});

export default HwatuStoryResult;
