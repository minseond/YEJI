import React, { useRef, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Quote, ArrowLeft, X, Download, Check } from 'lucide-react';
import { toPng } from 'html-to-image';
import KoreanSeal from '../../assets/ui/korean_seal.png';
import { useCharacterSettings, getCharacterImage, getCharacterName } from '../../utils/character';

interface HwatuSummaryResultProps {
    data: {
        cards: Array<{
            name: string;
            img: string;
            type: string;
            desc: string;
            detailedDesc: string;
        }>;
        vibe: string;
        keyword: string;
        summary: string;
        report: string;
        lucky?: {
            color: string;
            number: string;
            direction: string;
            timing: string;
            element?: string;
        };
    };
    onRestart: () => void;
    onExit: () => void;
    onBack: () => void;
    mode?: 'default' | 'history';
}

const HwatuSummaryResult: React.FC<HwatuSummaryResultProps> = React.memo(({ data, onRestart, onExit, onBack, mode = 'default' }) => {
    const [selectedCard, setSelectedCard] = useState<typeof data.cards[0] | null>(null);
    // Phase 1: Get equipped character settings from collection
    const settings = useCharacterSettings();
    const equippedEastId = settings.east; // 'soiseol', 'sinseon', 'buchae_woman' etc.

    const getColorData = (colorName: string) => {
        const colorMap: Record<string, { bg: string, hex: string }> = {
            '빨간색': { bg: 'bg-red-100/60', hex: '#ff4d4d' },
            '홍색': { bg: 'bg-red-100/60', hex: '#ff4d4d' },
            '빨강': { bg: 'bg-red-100/60', hex: '#ff4d4d' },
            '파란색': { bg: 'bg-blue-100/60', hex: '#4da3ff' },
            '청색': { bg: 'bg-blue-100/60', hex: '#4da3ff' },
            '파랑': { bg: 'bg-blue-100/60', hex: '#4da3ff' },
            '남색': { bg: 'bg-indigo-100/60', hex: '#6366f1' },
            '노란색': { bg: 'bg-yellow-100/60', hex: '#fbbf24' },
            '황색': { bg: 'bg-yellow-100/60', hex: '#fbbf24' },
            '노랑': { bg: 'bg-yellow-100/60', hex: '#fbbf24' },
            '초록색': { bg: 'bg-emerald-100/60', hex: '#34d399' },
            '녹색': { bg: 'bg-emerald-100/60', hex: '#34d399' },
            '초록': { bg: 'bg-emerald-100/60', hex: '#34d399' },
            '보라색': { bg: 'bg-purple-100/60', hex: '#a855f7' },
            '자색': { bg: 'bg-purple-100/60', hex: '#a855f7' },
            '보라': { bg: 'bg-purple-100/60', hex: '#a855f7' },
            '검은색': { bg: 'bg-stone-200/60', hex: '#444444' },
            '흑색': { bg: 'bg-stone-200/60', hex: '#444444' },
            '검정': { bg: 'bg-stone-200/60', hex: '#444444' },
            '흰색': { bg: 'bg-stone-100/60', hex: '#ffffff' },
            '백색': { bg: 'bg-stone-100/60', hex: '#ffffff' },
            '하양': { bg: 'bg-stone-100/60', hex: '#ffffff' },
            '분홍색': { bg: 'bg-pink-100/60', hex: '#f472b6' },
            '분홍': { bg: 'bg-pink-100/60', hex: '#f472b6' },
            '주황색': { bg: 'bg-orange-100/60', hex: '#fb923c' },
            '주황': { bg: 'bg-orange-100/60', hex: '#fb923c' },
            '황금색': { bg: 'bg-yellow-100/60', hex: '#fcd34d' },
            '금색': { bg: 'bg-yellow-100/60', hex: '#fcd34d' },
        };
        return colorMap[colorName] || { bg: 'bg-amber-100/60', hex: '#d97706' };
    };

    const luckyItems = useMemo(() => {
        if (!data.lucky) return [];
        const colorData = getColorData(data.lucky.color);
        return [
            { label: '행운의 색상', value: data.lucky.color, symbol: '彩', meaning: '색', hex: colorData.hex },
            { label: '행운의 숫자', value: data.lucky.number, symbol: '數', meaning: '수', hex: colorData.hex },
            { label: '행운의 방위', value: data.lucky.direction, symbol: '方', meaning: '방', hex: colorData.hex },
            { label: '행운의 시간', value: data.lucky.timing, symbol: '時', meaning: '시', hex: colorData.hex },
        ];
    }, [data.lucky]);

    const reportRef = useRef<HTMLDivElement>(null);

    const handleDownload = async () => {
        if (!reportRef.current) return;

        try {
            const width = reportRef.current.scrollWidth;
            const height = reportRef.current.scrollHeight;

            const dataUrl = await toPng(reportRef.current, {
                cacheBust: true,
                width: width,
                height: height,
                pixelRatio: 2,
                style: {
                    borderRadius: '0',
                    margin: '0',
                    transform: 'none',
                }
            });
            const link = document.createElement('a');
            link.download = `예지-화투보고서-${data.keyword || '오늘의운세'}.png`;
            link.href = dataUrl;
            link.click();
        } catch (err) {
            console.error('oops, something went wrong!', err);
        }
    };

    return (
        <>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute inset-0 z-[70] overflow-y-auto bg-[#0a0908] custom-scrollbar"
            >
                {/* Top Navigation - Shared mystical style */}
                <div className={`fixed top-8 left-8 right-8 z-[100] flex ${mode === 'history' ? 'justify-end' : 'justify-between'} items-center pointer-events-none`}>
                    {mode === 'history' ? (
                        <motion.button
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            onClick={onBack}
                            className="pointer-events-auto flex items-center gap-2 px-6 py-2 rounded-full bg-amber-600/20 border border-amber-500/30 text-amber-100 shadow-xl hover:bg-amber-600/40 backdrop-blur-xl transition-all font-bold group"
                        >
                            <span>목록으로</span>
                            <ArrowLeft size={20} className="rotate-180 group-hover:translate-x-1 transition-transform" />
                        </motion.button>
                    ) : (
                        <>
                            <motion.button
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                onClick={onBack}
                                className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-stone-900/60 border border-amber-900/40 text-amber-100 shadow-xl hover:bg-stone-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                            >
                                <ArrowLeft size={18} />
                                뒤로가기
                            </motion.button>

                            <motion.button
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                onClick={onExit}
                                className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-stone-900/60 border border-amber-900/40 text-amber-100 shadow-xl hover:bg-stone-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                            >
                                나가기
                                <X size={18} />
                            </motion.button>
                        </>
                    )}
                </div>

                {/* The "Document" Container */}
                <div
                    ref={reportRef}
                    className="max-w-5xl mx-auto my-16 md:my-24 relative z-10 bg-[#fdfcf5] text-stone-900 rounded-[2rem] shadow-[0_40px_100px_rgba(0,0,0,0.8),inset_0_0_100px_rgba(139,69,19,0.05)] border-4 border-double border-amber-900/30 overflow-hidden"
                >
                    {/* Rice Paper Texture Overlay */}
                    <div className="absolute inset-0 opacity-[0.08] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/rice-paper.png')]" />

                    <div className="relative z-10 p-6 md:p-16 flex flex-col items-center">
                        {/* Header Section */}
                        {/* Header Section */}
                        <div className="w-full flex flex-col items-center text-center gap-4 border-b-2 border-double border-amber-900/20 pb-8 pt-6">
                            <div className="space-y-4">
                                <div className="flex items-center justify-center gap-3">
                                    <span className="px-10 py-5 border-2 border-amber-950/40 font-bold tracking-[0.2em] font-['Hahmlet'] transition-all">
                                        <span className="text-4xl md:text-6xl bg-gradient-to-b from-amber-950 to-amber-700 bg-clip-text text-transparent">
                                            화투 점괘 보고서
                                        </span>
                                    </span>
                                </div>
                                <div className="space-y-2">
                                    <div className="w-80 h-[2px] bg-gradient-to-r from-transparent via-amber-900/40 to-transparent mx-auto mt-4" />
                                    <p className="text-amber-800/60 text-base mt-4 tracking-[0.2em] font-bold font-['Hahmlet']">화투 속에 담긴 운명의 조각</p>
                                </div>
                            </div>
                        </div>

                        {/* Content Section */}
                        <div className="mt-10 w-full space-y-12">
                            {/* 1. 청운도사의 점괘 풀이 (Narrative Analysis Section) */}
                            <section className="space-y-6">
                                <div className="flex flex-col items-center gap-2">
                                    <div className="flex items-center justify-center gap-4 ml-4 md:ml-8">
                                        <h2 className="text-3xl md:text-5xl font-['Hahmlet'] font-bold text-amber-900 text-center tracking-tight leading-none">
                                            {getCharacterName('east', equippedEastId)}의 점괘 풀이
                                        </h2>
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.8, x: -10 }}
                                            animate={{ opacity: 1, scale: 1, x: 0 }}
                                            className="relative w-32 h-32 md:w-40 md:h-40 shrink-0"
                                        >
                                            <img
                                                src={getCharacterImage('east', equippedEastId, 'loading') || '/assets/character/east/sinseon/sinseon_loading4.png'}
                                                alt={getCharacterName('east', equippedEastId)}
                                                className="w-full h-full object-contain filter drop-shadow-md"
                                            />
                                        </motion.div>
                                    </div>
                                    <div className="w-20 h-1.5 bg-amber-900/10 rounded-full" />
                                </div>

                                <div className="relative bg-[#faf7ec] border border-amber-950/10 rounded-[2.5rem] p-8 md:p-16 shadow-sm overflow-hidden">
                                    {/* Visual Decoration */}
                                    <div className="absolute top-0 right-0 w-64 h-64 bg-amber-900/5 -translate-y-32 translate-x-32 rotate-45 border-b border-amber-900/10" />

                                    <div className="relative z-20 flex flex-col gap-6">
                                        {/* Top: Advice Section (Advice Text + Character) */}
                                        <div className="w-full space-y-8 font-['Hahmlet']">
                                            {/* Keyword */}
                                            <div className="space-y-2">
                                                <div className="flex items-center gap-6">
                                                    <div className="text-3xl md:text-5xl font-bold bg-gradient-to-br from-amber-950 to-amber-700 bg-clip-text text-transparent py-2">
                                                        #{data.keyword}
                                                    </div>
                                                    <div className="h-1 bg-amber-950/10 flex-1 rounded-full" />
                                                </div>
                                            </div>

                                            {/* Summary */}
                                            <div className="relative group w-full">
                                                <p className="text-xl md:text-2xl lg:text-3xl leading-snug text-amber-950 font-bold break-keep italic border-l-8 border-amber-900/30 pl-6 transition-all drop-shadow-sm bg-amber-900/5 py-6 pr-6 rounded-r-2xl">
                                                    "{data.summary}"
                                                </p>
                                            </div>
                                        </div>

                                        {/* Bottom: Detailed Explanation Section - Divider Removed */}
                                        <div className="space-y-4">
                                            <div className="text-base md:text-lg font-bold text-amber-800/60 uppercase tracking-[0.4em] font-['Hahmlet'] flex items-center gap-3">
                                                상세 점괘 풀이
                                            </div>
                                            <div className="text-stone-800/90 text-sm md:text-lg lg:text-xl leading-snug break-keep space-y-4 text-left w-full font-['Hahmlet'] bg-white/50 p-6 md:p-10 rounded-[2rem] border border-amber-900/10 shadow-inner">
                                                {(() => {
                                                    const sentences = data.report.split(/(?<=[.!?])\s+/).map(s => s.trim());
                                                    return sentences
                                                        .filter(s => !s.includes('[조언]') && s.length > 0)
                                                        .map((sentence, sIdx) => (
                                                            <p key={sIdx} className="mb-3 text-stone-700/80">
                                                                {sentence}
                                                            </p>
                                                        ));
                                                })()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>

                            {/* Traditional Divider */}
                            <div className="flex items-center justify-center gap-6 py-4">
                                <div className="flex-1 h-[2px] bg-gradient-to-r from-transparent via-amber-900/20 to-transparent" />
                                <div className="flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-900/40" />
                                    <div className="w-3 h-3 border-2 border-amber-900/40 rotate-45" />
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-900/40" />
                                </div>
                                <div className="flex-1 h-[2px] bg-gradient-to-l from-transparent via-amber-900/20 to-transparent" />
                            </div>

                            {/* 2. 오늘의 행운 (Lucky Factors) - Horizontal Layout */}
                            {data.lucky && (
                                <section className="space-y-6">
                                    <header className="flex flex-col items-center gap-4">
                                        <h2 className="text-2xl font-['Hahmlet'] font-bold text-amber-900 flex items-center justify-center gap-4">
                                            <Quote size={20} className="text-amber-700 opacity-50 rotate-180" />
                                            행운의 부적
                                            <Quote size={20} className="text-amber-700 opacity-50" />
                                        </h2>
                                        <div className="w-12 h-1 bg-amber-900/10 rounded-full" />
                                    </header>

                                    <div className="relative">
                                        {/* Global Mystical Glow Background */}
                                        <motion.div
                                            animate={{
                                                opacity: [0.15, 0.3, 0.15],
                                                scale: [0.8, 1.2, 0.8],
                                            }}
                                            transition={{
                                                duration: 8,
                                                repeat: Infinity,
                                                ease: "easeInOut",
                                            }}
                                            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl h-full blur-[120px] rounded-full pointer-events-none z-0"
                                            style={{ backgroundColor: luckyItems[0]?.hex || '#d97706' }}
                                        />

                                        <div className="relative z-10 flex flex-nowrap items-start justify-center gap-4 md:gap-8 lg:gap-12 px-4 pt-12 pb-20 overflow-x-auto custom-scrollbar no-scrollbar lg:overflow-visible">
                                            {luckyItems.map((item, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, scale: 0.85, y: 60, rotate: (i % 2 === 0 ? -3 : 3) }}
                                                    whileInView={{
                                                        opacity: 1,
                                                        scale: 1,
                                                        y: 0,
                                                        rotate: [i % 2 === 0 ? -1.5 : 1.5, i % 2 === 0 ? 1.5 : -1.5, i % 2 === 0 ? -1.5 : 1.5]
                                                    }}
                                                    viewport={{ once: true }}
                                                    animate={{
                                                        rotate: [i % 2 === 0 ? -1.5 : 1.5, i % 2 === 0 ? 1.5 : -1.5, i % 2 === 0 ? -1.5 : 1.5]
                                                    }}
                                                    transition={{
                                                        delay: 0.3 + i * 0.12,
                                                        type: "spring",
                                                        damping: 14,
                                                        stiffness: 100,
                                                        rotate: {
                                                            duration: 5 + i,
                                                            repeat: Infinity,
                                                            ease: "easeInOut"
                                                        }
                                                    }}
                                                    whileHover={{
                                                        y: -20,
                                                        scale: 1.08,
                                                        rotate: 0,
                                                        transition: { type: "spring", stiffness: 400, damping: 10 }
                                                    }}
                                                    className="relative group flex-1 min-w-[140px] max-w-[200px]"
                                                >
                                                    {/* Mystical Glow Background */}
                                                    <div className="absolute inset-0 bg-gradient-radial from-amber-400/20 via-transparent to-transparent blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 scale-150" />

                                                    {/* Hanging String with Knot */}
                                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-8 w-[2.5px] h-16 bg-gradient-to-b from-amber-900/30 via-stone-800 to-stone-900 shadow-sm" />
                                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-10 w-3 h-3 rounded-full border-2 border-amber-950 bg-amber-700 shadow-md group-hover:scale-125 transition-transform" />

                                                    {/* Main Talisman Slip with Premium Effects */}
                                                    <div className="relative mx-auto w-full min-h-[300px] md:min-h-[340px] bg-[#fdfcf5] border-2 border-red-900/20 py-10 px-4 shadow-[0_15px_35px_-12px_rgba(139,69,19,0.3)] flex flex-col justify-between items-center gap-5 overflow-visible rounded-[3px] transition-all duration-500 group-hover:shadow-[0_25px_65px_-15px_rgba(139,69,19,0.5)] group-hover:border-red-900/40">
                                                        {/* Folded paper effects (left/right subtle shadows) */}
                                                        <div className="absolute inset-y-0 left-0 w-[5%] bg-gradient-to-r from-black/5 to-transparent pointer-events-none" />
                                                        <div className="absolute inset-y-0 right-0 w-[5%] bg-gradient-to-l from-black/5 to-transparent pointer-events-none" />

                                                        {/* Rich Hanji Texture with Grain */}
                                                        <div className="absolute inset-0 opacity-[0.15] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/natural-paper.png')] mix-blend-multiply" />


                                                        {/* Horizontal Label with Calligraphy Style */}
                                                        <div className="text-xs md:text-sm font-bold text-amber-900/60 font-['Hahmlet'] tracking-[0.2em] opacity-80 group-hover:opacity-100 group-hover:text-amber-900 transition-all duration-300">
                                                            {item.label}
                                                        </div>

                                                        {/* Elegant Divider */}
                                                        <div className="w-full flex items-center gap-1">
                                                            <div className="flex-1 h-[1px] bg-gradient-to-r from-transparent via-amber-900/40 to-transparent" />
                                                            <div className="w-1.5 h-1.5 border border-amber-900/20 rotate-45" />
                                                            <div className="flex-1 h-[1px] bg-gradient-to-l from-transparent via-amber-900/40 to-transparent" />
                                                        </div>

                                                        {/* Middle Section: Main Content with Enhanced Typography - Dynamic resizing for Lucky Time */}
                                                        <div className="relative z-10 flex flex-col items-center flex-1 justify-center text-center px-1 w-full scale-100">
                                                            <div className={`relative z-10 font-bold font-['Hahmlet'] text-amber-950 leading-snug tracking-tighter transition-all duration-300 group-hover:scale-105 drop-shadow-sm break-keep
                                                            ${item.label === '행운의 시간' || item.value.length > 8 ? 'text-lg md:text-xl lg:text-2xl' :
                                                                    item.value.length > 5 ? 'text-2xl md:text-3xl lg:text-4xl' :
                                                                        'text-3xl md:text-4xl lg:text-5xl'}`}>
                                                                {item.value}
                                                            </div>
                                                        </div>

                                                        {/* Traditional Talisman Seal with Chinese Character and Hover Meaning */}
                                                        <div className="mt-4 relative mb-2">
                                                            {/* Seal Box */}
                                                            <div className="relative w-16 h-16 md:w-20 md:h-20 bg-gradient-to-br from-red-900/10 to-red-950/10 flex items-center justify-center transform rotate-2 group-hover:rotate-0 transition-all duration-500 border-2 border-red-900/50 group-hover:border-red-900/80 overflow-hidden group/seal">
                                                                {/* Chinese Character */}
                                                                <motion.div
                                                                    className="relative z-10 text-4xl md:text-5xl font-bold text-red-900/90 mix-blend-multiply transition-all duration-300 font-['Hahmlet'] drop-shadow-sm"
                                                                    whileHover={{ opacity: 0, scale: 0.8 }}
                                                                >
                                                                    {item.symbol}
                                                                </motion.div>

                                                                {/* Hover Meaning Overlay */}
                                                                <div className="absolute inset-0 flex items-center justify-center bg-red-900/5 opacity-0 group-hover/seal:opacity-100 transition-opacity duration-300 pointer-events-none">
                                                                    <div className="text-amber-950 font-['Hahmlet'] font-bold text-xl md:text-2xl tracking-tighter">
                                                                        {item.meaning}
                                                                    </div>
                                                                </div>

                                                                {/* Seal Internal Decorative Frame */}
                                                                <div className="absolute inset-1.5 border border-red-950/20" />
                                                            </div>
                                                        </div>

                                                        {/* Corner Ornaments */}
                                                        <div className="absolute top-2 left-2 w-3 h-3 border-l-2 border-t-2 border-amber-950/10" />
                                                        <div className="absolute top-2 right-2 w-3 h-3 border-r-2 border-t-2 border-amber-950/10" />
                                                        <div className="absolute bottom-2 left-2 w-3 h-3 border-l-2 border-b-2 border-amber-950/10" />
                                                        <div className="absolute bottom-2 right-2 w-3 h-3 border-r-2 border-b-2 border-amber-950/10" />

                                                        {/* Norigae Tassel (Decorative traditional strings at bottom) */}
                                                        <div className="absolute -bottom-24 left-1/2 -translate-x-1/2 flex flex-col items-center pointer-events-none group-hover:translate-y-2 transition-transform duration-500">
                                                            {/* Top thread connecting to paper */}
                                                            <div className="w-[1.5px] h-6 bg-stone-800" />

                                                            {/* Traditional Decorative Knot (Maedeup) */}
                                                            <div className="relative w-6 h-6 flex items-center justify-center">
                                                                <div className="absolute inset-0 bg-red-900 rotate-45 rounded-sm shadow-sm" />
                                                                <div className="absolute inset-1 border border-amber-500/20 rotate-45" />
                                                                <div className="w-2 h-2 rounded-full bg-amber-500/30 blur-[1px]" />
                                                            </div>

                                                            {/* Tassel threads */}
                                                            <div className="flex gap-[1.5px] mt-0.5">
                                                                {[...Array(6)].map((_, idx) => (
                                                                    <motion.div
                                                                        key={idx}
                                                                        animate={{
                                                                            rotate: [0, idx % 2 === 0 ? 1 : -1, 0],
                                                                            height: [40, 44, 40]
                                                                        }}
                                                                        transition={{
                                                                            duration: 3 + idx,
                                                                            repeat: Infinity,
                                                                            ease: "easeInOut"
                                                                        }}
                                                                        className="w-[2px] bg-gradient-to-b from-red-900/90 via-red-800/80 to-transparent rounded-full opacity-90 shadow-sm"
                                                                    />
                                                                ))}
                                                            </div>

                                                            {/* Metallic Cap or Gem inside Tassel */}
                                                            <div className="absolute top-[34px] w-4 h-4 rounded-full bg-gradient-to-tr from-amber-700 to-amber-400 blur-[2px] opacity-20" />
                                                        </div>
                                                    </div>

                                                </motion.div>
                                            ))}
                                        </div>
                                    </div>
                                </section>
                            )}

                            {/* Traditional Divider */}
                            <div className="flex items-center justify-center gap-6 py-4">
                                <div className="flex-1 h-[2px] bg-gradient-to-r from-transparent via-amber-900/20 to-transparent" />
                                <div className="flex items-center gap-2">
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-900/40" />
                                    <div className="w-3 h-3 border-2 border-amber-900/40 rotate-45" />
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-900/40" />
                                </div>
                                <div className="flex-1 h-[2px] bg-gradient-to-l from-transparent via-amber-900/20 to-transparent" />
                            </div>

                            {/* 3. 개별 카드 상세 분석 (Card Breakdown) */}
                            <section className="space-y-8 pb-8 w-full">
                                <header className="flex flex-col items-center gap-4 mb-8">
                                    <h2 className="text-2xl font-['Hahmlet'] font-bold text-amber-900 flex items-center justify-center gap-4">
                                        <Quote size={20} className="text-amber-700 opacity-50 rotate-180" />
                                        그대가 선택한 네 장의 패
                                        <Quote size={20} className="text-amber-700 opacity-50" />
                                    </h2>
                                    <div className="w-12 h-1 bg-amber-900/10 rounded-full" />
                                </header>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                                    {data.cards.map((card, idx) => (
                                        <motion.div
                                            key={idx}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 1 + idx * 0.1 }}
                                            onClick={() => setSelectedCard(card)}
                                            className="group relative bg-white/60 border border-amber-900/10 rounded-xl p-8 hover:bg-white transition-all overflow-hidden shadow-sm flex flex-col items-center cursor-pointer active:scale-95"
                                        >
                                            <div className="absolute inset-0 opacity-[0.05] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/rice-paper-2.png')]" />
                                            <div className="relative flex flex-col items-center gap-6 w-full">
                                                <div className="text-xs tracking-[0.3em] text-amber-900/70 font-bold font-['Hahmlet'] uppercase bg-amber-50/80 px-3 py-1.5 rounded-full border border-amber-900/20">
                                                    {card.type === '광' ? '光 (광)' :
                                                        card.type === '피' ? '皮 (피)' :
                                                            card.type === '띠' ? '띠 (청단/홍단/초단)' :
                                                                card.type === '끗' ? '끗 (열끗)' : card.type}
                                                </div>
                                                <div className="relative w-32 h-48 rounded-lg overflow-hidden border-2 border-amber-950/20 shadow-md transform group-hover:-rotate-2 transition-transform duration-500">
                                                    <img src={card.img} alt={card.name} className="w-full h-full object-cover" />
                                                    <div className="absolute inset-0 border border-white/20 pointer-events-none" />
                                                </div>
                                                <div className="text-center space-y-4 w-full">
                                                    <h4 className="text-xl font-bold font-['Hahmlet'] text-amber-950">{card.name}</h4>
                                                    <div className="text-[12px] text-amber-800 font-bold italic border-y border-amber-900/5 py-2">"{card.desc}"</div>
                                                    <p className="mt-4 text-[11px] font-bold text-amber-900/40 uppercase tracking-widest">
                                                        자세히 보기
                                                    </p>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </section>
                        </div>

                        {/* Oriental Seal branding section */}
                        <div className="flex flex-col items-center mt-10 mb-4 w-full">
                            <div className="w-full max-w-xs h-[1px] bg-gradient-to-r from-transparent via-amber-900/10 to-transparent mb-8" />
                            <motion.div
                                initial={{ opacity: 0, scale: 1.2, rotate: -15 }}
                                whileInView={{ opacity: 0.8, scale: 1, rotate: -5 }}
                                viewport={{ once: true }}
                                transition={{ type: "spring", damping: 15 }}
                                className="relative"
                            >
                                <img src={KoreanSeal} alt="공식 인장" className="w-24 h-24 object-contain mix-blend-multiply filter contrast-125 brightness-95 opacity-80" />
                            </motion.div>
                        </div>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="flex flex-col md:flex-row items-center justify-center gap-6 pt-6 pb-12 relative z-20">
                    <button
                        onClick={handleDownload}
                        className="w-full md:w-auto flex items-center justify-center gap-3 px-10 py-5 bg-white/5 hover:bg-white/10 border border-white/20 rounded-full text-white transition-all font-bold text-lg shadow-xl backdrop-blur-sm"
                    >
                        <Download size={22} className="text-amber-400" /> 이미지 저장하기
                    </button>

                    <button
                        onClick={onRestart}
                        className="w-full md:w-auto flex items-center justify-center gap-3 px-16 py-5 bg-amber-900 text-amber-50 hover:bg-amber-800 border border-amber-600/30 rounded-full transition-all font-bold text-lg shadow-xl"
                    >
                        <Check size={22} /> 완료
                    </button>
                </div>

                {/* AI Disclaimer Footnote */}
                <div className="max-w-2xl mx-auto text-center px-6 pb-24 md:pb-32">
                    <p className="italic text-[11px] text-white/20 font-['Hahmlet'] leading-relaxed break-keep">
                        * 본 보고서는 예지 AI가 분석한 점괘 기록이며, 미래를 확정하거나 법적 책임을 지지 않습니다. <br className="hidden md:block" /> 모든 운 흐름은 참고용으로만 활용해 주시기 바랍니다.
                    </p>
                </div>
            </motion.div>

            {/* Card Detail Modal */}
            <AnimatePresence>
                {selectedCard && (
                    <div className="fixed inset-0 z-[150] flex items-center justify-center p-4 md:p-8">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSelectedCard(null)}
                            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            className="relative w-full max-w-2xl bg-[#fdfcf5] rounded-[2rem] shadow-2xl overflow-hidden border-2 border-amber-900/30 font-['Hahmlet']"
                        >
                            {/* Paper texture */}
                            <div className="absolute inset-0 opacity-[0.05] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/rice-paper.png')]" />

                            <button
                                onClick={() => setSelectedCard(null)}
                                className="absolute top-6 right-6 p-2 rounded-full hover:bg-stone-200/50 transition-colors z-20"
                            >
                                <X size={24} className="text-stone-600" />
                            </button>

                            <div className="relative z-10 p-8 md:p-12 flex flex-col md:flex-row gap-8 md:gap-12">
                                {/* Left: Card Image */}
                                <div className="w-full md:w-48 shrink-0 flex flex-col items-center gap-4">
                                    <div className="relative w-40 h-60 rounded-xl overflow-hidden border-4 border-amber-900/10 shadow-xl">
                                        <img src={selectedCard.img} alt={selectedCard.name} className="w-full h-full object-cover" />
                                        <div className="absolute inset-0 border border-white/20 pointer-events-none" />
                                    </div>
                                    <div className="text-xs font-bold text-amber-900/60 tracking-[0.3em] uppercase">
                                        {selectedCard.type}
                                    </div>
                                </div>

                                {/* Right: Card Text */}
                                <div className="flex-1 space-y-6">
                                    <div className="space-y-2">
                                        <h3 className="text-3xl font-bold text-amber-950">{selectedCard.name}</h3>
                                        <div className="text-lg text-amber-800 font-bold italic">"{selectedCard.desc}"</div>
                                    </div>

                                    <div className="w-full h-[1px] bg-gradient-to-r from-amber-900/20 to-transparent" />

                                    <div className="space-y-4">
                                        <p className="text-stone-700/90 text-base md:text-lg leading-[1.8] break-keep">
                                            {selectedCard.detailedDesc}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </>
    );
});

export default HwatuSummaryResult;
