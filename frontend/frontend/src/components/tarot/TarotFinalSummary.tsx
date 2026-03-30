import { motion } from 'framer-motion';
import { Home, Share2, RefreshCw, Trophy, Star, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import FateRadarChart from './FateRadarChart';
import { useMemo, useState, useEffect } from 'react';

interface CardSummary {
    stepTitle: string;
    cardName: string;
    isReversed: boolean;
    cardImageUrl?: string;
}

interface TarotFinalSummaryProps {
    cards: CardSummary[];
    overallSummary: string;
    onRestart?: () => void;
    onShuffle?: () => void;
}

type FateGrade = 'S' | 'A' | 'B' | 'C';

const TarotFinalSummary = ({ cards, overallSummary, onRestart, onShuffle }: TarotFinalSummaryProps) => {
    const navigate = useNavigate();
    const [showRank, setShowRank] = useState(false);

    // Calculate Game Stats based on card names (deterministic random)
    const stats = useMemo(() => {
        const seed = cards.reduce((acc, c) => acc + c.cardName.length, 0);
        const rand = (offset: number) => ((seed + offset) * 9301 + 49297) % 233280 / 233280;

        return {
            love: 70 + Math.floor(rand(1) * 30),
            money: 65 + Math.floor(rand(2) * 35),
            career: 75 + Math.floor(rand(3) * 25),
            health: 80 + Math.floor(rand(4) * 20),
            luck: 60 + Math.floor(rand(5) * 40),
        };
    }, [cards]);

    // Calculate Rank
    const rank: FateGrade = useMemo(() => {
        const avg = Object.values(stats).reduce((a, b) => a + b, 0) / 5;
        if (avg >= 90) return 'S';
        if (avg >= 85) return 'A';
        if (avg >= 75) return 'B';
        return 'C';
    }, [stats]);

    // Show Rank Animation trigger
    useEffect(() => {
        setTimeout(() => setShowRank(true), 800);
    }, []);

    const handleShare = () => {
        alert('결과 공유 기능 준비 중입니다!');
    };

    const rankColors = {
        S: 'text-yellow-400 drop-shadow-[0_0_15px_rgba(250,204,21,0.8)]',
        A: 'text-purple-400 drop-shadow-[0_0_15px_rgba(192,132,252,0.8)]',
        B: 'text-blue-400 drop-shadow-[0_0_15px_rgba(96,165,250,0.8)]',
        C: 'text-gray-400 drop-shadow-[0_0_10px_rgba(156,163,175,0.5)]',
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center h-screen overflow-y-auto p-4 md:p-8 bg-[url('/assets/bg/space_bg.jpg')] bg-cover bg-center bg-fixed custom-scrollbar"
        >
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm fixed" />

            <div className="relative max-w-4xl w-full z-10 flex flex-col gap-12 py-10 shrink-0">

                {/* 1. Cards (Artifact Slots) - Top */}
                <motion.div
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="flex flex-col items-center"
                >
                    {/* Header Removed as requested */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-4">
                        {cards.map((card, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.3 + idx * 0.1 }}
                                className="relative group bg-slate-900/60 border border-purple-500/30 rounded-xl p-3 flex flex-col gap-3 hover:bg-slate-800/60 transition-colors shadow-lg hover:shadow-purple-500/10"
                            >
                                {/* Slot Header */}
                                <div className="flex justify-between items-center px-1">
                                    <span className="text-[10px] text-purple-300 uppercase tracking-wider font-bold">{card.stepTitle}</span>
                                    {card.isReversed && (
                                        <span className="bg-red-900/80 text-red-200 text-[10px] px-1.5 py-0.5 rounded border border-red-500/30">REV</span>
                                    )}
                                </div>

                                {/* Card Image Slot */}
                                <div className="relative aspect-[2/3] w-full rounded-lg overflow-hidden border border-slate-600 group-hover:border-purple-400/50 transition-colors shadow-inner bg-black/50">
                                    {card.cardImageUrl ? (
                                        <img
                                            src={card.cardImageUrl}
                                            alt={card.cardName}
                                            className="w-full h-full object-cover"
                                            style={{ transform: card.isReversed ? 'rotate(180deg)' : 'rotate(0deg)' }}
                                        />
                                    ) : (
                                        <div className="w-full h-full bg-slate-800 flex items-center justify-center">
                                            <span className="text-slate-600 text-xs">No Image</span>
                                        </div>
                                    )}
                                    <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent pointer-events-none" />
                                </div>

                                {/* Card Name Footer */}
                                <div className="text-center pb-1">
                                    <div className="text-purple-100 font-['Cinzel'] text-sm truncate">{card.cardName}</div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>

                {/* 2. Rank Stamp */}
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.6 }}
                    className="flex flex-col items-center justify-center p-8 bg-slate-900/40 border-y border-white/5 backdrop-blur-sm"
                >
                    <div className="text-slate-400 text-xs tracking-widest uppercase mb-4">Fate Rank Evaluation</div>
                    {showRank && (
                        <motion.div
                            initial={{ scale: 3, opacity: 0, rotate: -20 }}
                            animate={{ scale: 1.2, opacity: 1, rotate: 0 }}
                            transition={{ type: "spring", stiffness: 200, damping: 15 }}
                            className={`text-9xl font-['Cinzel'] font-black ${rankColors[rank]}`}
                        >
                            {rank}
                        </motion.div>
                    )}
                </motion.div>

                {/* 3. Stats Radar */}
                <motion.div
                    initial={{ y: 30, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.8 }}
                    className="flex flex-col items-center"
                >
                    <h3 className="text-purple-300/80 text-sm tracking-[0.3em] font-bold mb-6 font-['Cinzel']">FATE SPECS</h3>
                    <div className="bg-slate-900/80 border border-slate-700/50 rounded-2xl p-8 flex flex-col items-center justify-center relative w-full max-w-md">
                        <div className="w-full aspect-square max-w-[300px] flex items-center justify-center">
                            <FateRadarChart stats={stats} color={rank === 'S' || rank === 'A' ? '#c084fc' : '#60a5fa'} />
                        </div>
                        <div className="flex gap-4 text-[10px] text-slate-500 mt-4 font-mono">
                            <span>LUC: {stats.luck}</span>
                            <span>LOV: {stats.love}</span>
                            <span>MNY: {stats.money}</span>
                            <span>CAR: {stats.career}</span>
                            <span>HLT: {stats.health}</span>
                        </div>
                    </div>
                </motion.div>

                {/* 4. Overall Summary */}
                <motion.div
                    initial={{ y: 30, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 1.0 }}
                    className="flex flex-col items-center w-full"
                >
                    <h3 className="text-purple-300/80 text-sm tracking-[0.3em] font-bold mb-6 font-['Cinzel']">ANALYSIS LOG</h3>
                    <div className="w-full bg-slate-900/80 border border-slate-700/50 rounded-2xl p-6 md:p-8 shadow-2xl relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity pointer-events-none">
                            <Sparkles className="w-32 h-32 text-purple-400" />
                        </div>

                        <div className="bg-black/30 rounded-xl p-6 border border-white/5">
                            <p className="text-slate-300 font-['Pretendard'] leading-loose whitespace-pre-line text-base text-center">
                                {overallSummary}
                            </p>
                        </div>
                    </div>
                </motion.div>

                {/* 5. Action Bar */}
                <motion.div
                    initial={{ y: 50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 1.2 }}
                    className="flex flex-col md:flex-row gap-4 justify-center mt-8 pb-10"
                >
                    <button
                        onClick={handleShare}
                        className="px-8 py-4 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-slate-200 font-['GmarketSansBold'] flex items-center justify-center gap-2 transition-all group w-full md:w-auto"
                    >
                        <Share2 className="w-5 h-5 group-hover:text-purple-400 transition-colors" />
                        <span>SHARE</span>
                    </button>

                    {onShuffle && (
                        <button
                            onClick={onShuffle}
                            className="px-8 py-4 bg-slate-800 hover:bg-slate-700 border border-purple-500/30 hover:border-purple-500/60 rounded-xl text-purple-200 font-['GmarketSansBold'] flex items-center justify-center gap-2 transition-all group shadow-[0_0_15px_rgba(168,85,247,0.1)] w-full md:w-auto"
                        >
                            <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                            <span>REROLL</span>
                        </button>
                    )}

                    <button
                        onClick={() => navigate('/home')}
                        className="px-10 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 rounded-xl text-white font-['GmarketSansBold'] shadow-[0_0_20px_rgba(147,51,234,0.3)] hover:shadow-[0_0_30px_rgba(147,51,234,0.5)] transition-all flex items-center justify-center gap-2 w-full md:w-auto"
                    >
                        <Home className="w-5 h-5" />
                        <span>COMPLETE</span>
                    </button>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default TarotFinalSummary;
