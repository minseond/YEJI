import React, { useRef, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Quote, ArrowLeft, X, Download, Check, Sparkles } from 'lucide-react';
import { toPng } from 'html-to-image';
import type { CardResultDetailResponse } from '../../api/card';
import { getTarotImage } from '../../utils/tarotAssets';
import { useCharacterSettings, getCharacterName as getCharacterNameUtil } from '../../utils/character';

interface TarotResultViewProps {
    data: CardResultDetailResponse | null;
    onRestart: () => void;
    onExit: () => void;
    onBack: () => void;
    mode?: 'default' | 'history';
}

const TarotResultView: React.FC<TarotResultViewProps> = React.memo(({ data, onRestart, onExit, onBack, mode = 'default' }) => {
    const [selectedCard, setSelectedCard] = useState<typeof processedCards[0] | null>(null);

    if (!data || !data.aiReading?.success) {
        return (
            <div className="w-full h-full bg-[#0f172a] flex items-center justify-center">
                <div className="text-white/50 animate-pulse">결과를 불러오는 중입니다...</div>
            </div>
        );
    }

    const reading = data.aiReading.data;
    const settings = useCharacterSettings();
    const equippedWestId = settings.west;

    // Get western character name
    const characterName = getCharacterNameUtil('west', equippedWestId);

    // Process cards
    const processedCards = useMemo(() => {
        const cards = reading.cards || [];
        return [...cards]
            .sort((a: any, b: any) => (a.position || 0) - (b.position || 0))
            .map((card: any) => {
                const cardCode = card.card_code || card.cardCode;
                const cardName = card.card_name || card.cardName;
                const positionLabel = card.position_label || card.positionLabel || '';
                const orientationLabel = card.orientation_label || '';
                const interpretation = card.interpretation || '';
                const keywords = card.keywords || [];
                const isReversed = card.is_reversed !== undefined ? card.is_reversed : card.isReversed;

                return {
                    name: cardName,
                    img: getTarotImage(cardCode),
                    type: orientationLabel,
                    position: positionLabel,
                    desc: keywords.join(', ') || '신비로운 카드',
                    detailedDesc: interpretation,
                    isReversed: !!isReversed
                };
            });
    }, [reading.cards]);

    const getColorData = (colorName: string) => {
        const colorMap: Record<string, { bg: string, hex: string }> = {
            '빨간색': { bg: 'bg-red-500/20', hex: '#ef4444' },
            '홍색': { bg: 'bg-red-500/20', hex: '#ef4444' },
            '파란색': { bg: 'bg-blue-500/20', hex: '#3b82f6' },
            '청색': { bg: 'bg-blue-500/20', hex: '#3b82f6' },
            '노란색': { bg: 'bg-yellow-500/20', hex: '#eab308' },
            '황색': { bg: 'bg-yellow-500/20', hex: '#eab308' },
            '초록색': { bg: 'bg-emerald-500/20', hex: '#10b981' },
            '녹색': { bg: 'bg-emerald-500/20', hex: '#10b981' },
            '보라색': { bg: 'bg-purple-500/20', hex: '#a855f7' },
            '자색': { bg: 'bg-purple-500/20', hex: '#a855f7' },
            '검은색': { bg: 'bg-gray-500/20', hex: '#6b7280' },
            '흑색': { bg: 'bg-gray-500/20', hex: '#6b7280' },
            '흰색': { bg: 'bg-white/20', hex: '#f3f4f6' },
            '백색': { bg: 'bg-white/20', hex: '#f3f4f6' },
            '분홍색': { bg: 'bg-pink-500/20', hex: '#ec4899' },
            '주황색': { bg: 'bg-orange-500/20', hex: '#f97316' },
        };
        return colorMap[colorName] || { bg: 'bg-purple-500/20', hex: '#a855f7' };
    };

    const lucky = reading.lucky || {
        color: '보라색',
        number: '7',
        element: '공기',
        timing: '자정'
    };

    const luckyItems = useMemo(() => {
        const colorData = getColorData(lucky.color);
        return [
            { label: '행운의 색상', value: lucky.color, symbol: '✦', meaning: '색', hex: colorData.hex },
            { label: '행운의 숫자', value: lucky.number, symbol: '✧', meaning: '수', hex: colorData.hex },
            { label: '행운의 원소', value: lucky.element, symbol: '✵', meaning: '원소', hex: colorData.hex },
            { label: '행운의 시간', value: lucky.timing, symbol: '✶', meaning: '시', hex: colorData.hex },
        ];
    }, [lucky]);

    const summary = reading.summary?.overall_theme || '신비로운 운명의 흐름이 당신을 기다립니다.';
    const report = reading.summary?.advice || '타로가 전하는 메시지를 마음에 새기세요.';

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
            link.download = `예지-타로보고서-${new Date().toISOString().split('T')[0]}.png`;
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
                className="absolute inset-0 z-[70] overflow-y-auto bg-[#0a0515] custom-scrollbar"
            >
                {/* Top Navigation */}
                <div className={`fixed top-8 left-8 right-8 z-[100] flex ${mode === 'history' ? 'justify-end' : 'justify-between'} items-center pointer-events-none`}>
                    {mode === 'history' ? (
                        <motion.button
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            onClick={onBack}
                            className="pointer-events-auto flex items-center gap-2 px-6 py-2 rounded-full bg-purple-900/60 border border-purple-500/40 text-purple-100 shadow-xl hover:bg-purple-800/80 backdrop-blur-xl transition-all font-bold group"
                        >
                            <span>목록으로</span>
                            <ArrowLeft size={18} className="rotate-180 group-hover:translate-x-1 transition-transform" />
                        </motion.button>
                    ) : (
                        <>
                            <motion.button
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                onClick={onBack}
                                className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-purple-900/60 border border-purple-500/40 text-purple-100 shadow-xl hover:bg-purple-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                            >
                                <ArrowLeft size={18} />
                                뒤로가기
                            </motion.button>

                            <motion.button
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                onClick={onExit}
                                className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-purple-900/60 border border-purple-500/40 text-purple-100 shadow-xl hover:bg-purple-800/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                            >
                                완료
                                <X size={18} />
                            </motion.button>
                        </>
                    )}
                </div>

                {/* The "Document" Container */}
                <div
                    ref={reportRef}
                    className="max-w-5xl mx-auto my-16 md:my-24 relative z-10 bg-[#0f0a1e] text-purple-50 rounded-[2rem] shadow-[0_40px_100px_rgba(139,0,255,0.4),inset_0_0_100px_rgba(168,85,247,0.08)] border-4 border-double border-purple-400/50 overflow-hidden"
                >
                    {/* Cosmic Texture Overlay */}
                    <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />

                    <div className="relative z-10 p-6 md:p-16 flex flex-col items-center">
                        {/* Header Section */}
                        <div className="w-full flex flex-col items-center text-center gap-4 border-b-2 border-double border-purple-500/20 pb-8 pt-6">
                            <div className="space-y-4">
                                <div className="flex items-center justify-center gap-3">
                                    <span className="px-10 py-5 border-2 border-purple-500/40 font-bold tracking-[0.2em] font-['Hahmlet'] transition-all">
                                        <span className="text-4xl md:text-6xl bg-gradient-to-b from-purple-300 to-purple-500 bg-clip-text text-transparent">
                                            타로 점괘 보고서
                                        </span>
                                    </span>
                                </div>
                                <div className="space-y-2">
                                    <div className="w-80 h-[2px] bg-gradient-to-r from-transparent via-purple-500/40 to-transparent mx-auto mt-4" />
                                    <p className="text-purple-400/60 text-base mt-4 tracking-[0.2em] font-bold font-['Hahmlet']">타로 속에 담긴 운명의 메시지</p>
                                </div>
                            </div>
                        </div>

                        {/* Content Section */}
                        <div className="mt-10 w-full space-y-12">
                            {/* 1. 점괘 풀이 (Narrative Analysis Section) */}
                            <section className="space-y-6">
                                <div className="flex flex-col items-center gap-2">
                                    <div className="flex items-center justify-center gap-4 mr-4 md:mr-8">
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.8, x: 10 }}
                                            animate={{ opacity: 1, scale: 1, x: 0 }}
                                            className="relative w-32 h-32 md:w-40 md:h-40 shrink-0"
                                        >
                                            <img
                                                src={`/assets/character/west/${equippedWestId}/${equippedWestId}_loading.png`}
                                                alt={characterName}
                                                className="w-full h-full object-contain filter drop-shadow-[0_0_20px_rgba(168,85,247,0.5)]"
                                            />
                                        </motion.div>
                                        <h2 className="text-3xl md:text-5xl font-['Hahmlet'] font-bold text-purple-300 text-center tracking-tight leading-none">
                                            {characterName}의 점괘 풀이
                                        </h2>
                                    </div>
                                    <div className="w-20 h-1.5 bg-purple-500/10 rounded-full" />
                                </div>

                                <div className="relative bg-purple-900/20 border border-purple-400/20 rounded-[2.5rem] p-8 md:p-16 shadow-sm overflow-hidden">
                                    {/* Visual Decoration */}
                                    <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 -translate-y-32 translate-x-32 rotate-45 border-b border-purple-500/10" />

                                    <div className="relative z-20 flex flex-col gap-6">
                                        {/* Top: Advice Section */}
                                        <div className="w-full space-y-8 font-['Hahmlet']">
                                            {/* Summary */}
                                            <div className="relative group w-full">
                                                <p className="text-xl md:text-2xl lg:text-3xl leading-snug text-purple-200 font-bold break-keep italic border-l-8 border-purple-500/30 pl-6 transition-all drop-shadow-sm bg-purple-500/5 py-6 pr-6 rounded-r-2xl">
                                                    "{summary}"
                                                </p>
                                            </div>
                                        </div>

                                        {/* Bottom: Detailed Explanation Section */}
                                        <div className="space-y-4">
                                            <div className="text-base md:text-lg font-bold text-purple-300/80 uppercase tracking-[0.4em] font-['Hahmlet'] flex items-center gap-3">
                                                상세 점괘 풀이
                                            </div>
                                            <div className="text-purple-100/90 text-sm md:text-lg lg:text-xl leading-snug break-keep space-y-4 text-left w-full font-['Hahmlet'] bg-purple-950/30 p-6 md:p-10 rounded-[2rem] border border-purple-400/20 shadow-inner">
                                                {(() => {
                                                    const sentences = report.split(/(?<=[.!?])\s+/).map(s => s.trim());
                                                    return sentences
                                                        .filter(s => s.length > 0)
                                                        .map((sentence, sIdx) => (
                                                            <p key={sIdx} className="mb-3 text-purple-200/90">
                                                                {sentence}
                                                            </p>
                                                        ));
                                                })()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>

                            {/* Mystical Divider */}
                            <div className="flex items-center justify-center gap-6 py-4">
                                <div className="flex-1 h-[2px] bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />
                                <div className="flex items-center gap-2">
                                    <Sparkles size={16} className="text-purple-500/40" />
                                    <div className="w-3 h-3 border-2 border-purple-500/40 rotate-45" />
                                    <Sparkles size={16} className="text-purple-500/40" />
                                </div>
                                <div className="flex-1 h-[2px] bg-gradient-to-l from-transparent via-purple-500/20 to-transparent" />
                            </div>

                            {/* 2. 행운의 부적 (Lucky Factors) */}
                            <section className="space-y-6">
                                <header className="flex flex-col items-center gap-4">
                                    <h2 className="text-2xl font-['Hahmlet'] font-bold text-purple-300 flex items-center justify-center gap-4">
                                        <Quote size={20} className="text-purple-400 opacity-50 rotate-180" />
                                        행운의 별빛
                                        <Quote size={20} className="text-purple-400 opacity-50" />
                                    </h2>
                                    <div className="w-12 h-1 bg-purple-500/10 rounded-full" />
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
                                        style={{ backgroundColor: luckyItems[0]?.hex || '#a855f7' }}
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
                                                <div className="absolute inset-0 bg-gradient-radial from-purple-400/20 via-transparent to-transparent blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 scale-150" />

                                                {/* Hanging String */}
                                                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-8 w-[2.5px] h-16 bg-gradient-to-b from-purple-500/30 via-purple-700 to-purple-900 shadow-sm" />
                                                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-10 w-3 h-3 rounded-full border-2 border-purple-500 bg-purple-400 shadow-md group-hover:scale-125 transition-transform" />

                                                {/* Main Card */}
                                                <div className="relative mx-auto w-full min-h-[300px] md:min-h-[340px] bg-purple-950/40 border-2 border-purple-500/20 py-10 px-4 shadow-[0_15px_35px_-12px_rgba(168,85,247,0.3)] flex flex-col justify-between items-center gap-5 overflow-visible rounded-[3px] transition-all duration-500 group-hover:shadow-[0_25px_65px_-15px_rgba(168,85,247,0.5)] group-hover:border-purple-500/40">
                                                    {/* Cosmic Texture */}
                                                    <div className="absolute inset-0 opacity-[0.05] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] mix-blend-overlay" />

                                                    {/* Label */}
                                                    <div className="text-xs md:text-sm font-bold text-purple-400/60 font-['Hahmlet'] tracking-[0.2em] opacity-80 group-hover:opacity-100 group-hover:text-purple-300 transition-all duration-300">
                                                        {item.label}
                                                    </div>

                                                    {/* Divider */}
                                                    <div className="w-full flex items-center gap-1">
                                                        <div className="flex-1 h-[1px] bg-gradient-to-r from-transparent via-purple-500/40 to-transparent" />
                                                        <div className="w-1.5 h-1.5 border border-purple-500/20 rotate-45" />
                                                        <div className="flex-1 h-[1px] bg-gradient-to-l from-transparent via-purple-500/40 to-transparent" />
                                                    </div>

                                                    {/* Value */}
                                                    <div className="relative z-10 flex flex-col items-center flex-1 justify-center text-center px-1 w-full scale-100">
                                                        <div className={`relative z-10 font-bold font-['Hahmlet'] text-purple-200 leading-snug tracking-tighter transition-all duration-300 group-hover:scale-105 drop-shadow-sm break-keep
                                                        ${item.label === '행운의 시간' || (item.value && item.value.length > 8) ? 'text-lg md:text-xl lg:text-2xl' :
                                                                (item.value && item.value.length > 5) ? 'text-2xl md:text-3xl lg:text-4xl' :
                                                                    'text-3xl md:text-4xl lg:text-5xl'}`}>
                                                            {item.value}
                                                        </div>
                                                    </div>

                                                    {/* Symbol */}
                                                    <div className="mt-4 relative mb-2">
                                                        <div className="relative w-16 h-16 md:w-20 md:h-20 bg-gradient-to-br from-purple-500/10 to-purple-700/10 flex items-center justify-center transform rotate-2 group-hover:rotate-0 transition-all duration-500 border-2 border-purple-500/50 group-hover:border-purple-400/80 overflow-hidden">
                                                            <div className="relative z-10 text-4xl md:text-5xl font-bold text-purple-400/90 transition-all duration-300 font-['Hahmlet'] drop-shadow-sm">
                                                                {item.symbol}
                                                            </div>

                                                            <div className="absolute inset-1.5 border border-purple-500/20" />
                                                        </div>
                                                    </div>

                                                    {/* Corner Ornaments */}
                                                    <div className="absolute top-2 left-2 w-3 h-3 border-l-2 border-t-2 border-purple-500/10" />
                                                    <div className="absolute top-2 right-2 w-3 h-3 border-r-2 border-t-2 border-purple-500/10" />
                                                    <div className="absolute bottom-2 left-2 w-3 h-3 border-l-2 border-b-2 border-purple-500/10" />
                                                    <div className="absolute bottom-2 right-2 w-3 h-3 border-r-2 border-b-2 border-purple-500/10" />
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                </div>
                            </section>

                            {/* Mystical Divider */}
                            <div className="flex items-center justify-center gap-6 py-4">
                                <div className="flex-1 h-[2px] bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />
                                <div className="flex items-center gap-2">
                                    <Sparkles size={16} className="text-purple-500/40" />
                                    <div className="w-3 h-3 border-2 border-purple-500/40 rotate-45" />
                                    <Sparkles size={16} className="text-purple-500/40" />
                                </div>
                                <div className="flex-1 h-[2px] bg-gradient-to-l from-transparent via-purple-500/20 to-transparent" />
                            </div>

                            {/* 3. 개별 카드 상세 분석 (Card Breakdown) */}
                            <section className="space-y-8 pb-8 w-full">
                                <header className="flex flex-col items-center gap-4 mb-8">
                                    <h2 className="text-2xl font-['Hahmlet'] font-bold text-purple-300 flex items-center justify-center gap-4">
                                        <Quote size={20} className="text-purple-400 opacity-50 rotate-180" />
                                        그대가 선택한 세 장의 카드
                                        <Quote size={20} className="text-purple-400 opacity-50" />
                                    </h2>
                                    <div className="w-12 h-1 bg-purple-500/10 rounded-full" />
                                </header>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                    {processedCards.map((card, idx) => (
                                        <motion.div
                                            key={idx}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 1 + idx * 0.1 }}
                                            onClick={() => setSelectedCard(card)}
                                            className="group relative bg-purple-950/30 border border-purple-500/10 rounded-xl p-8 hover:bg-purple-950/50 transition-all overflow-hidden shadow-sm flex flex-col items-center cursor-pointer active:scale-95"
                                        >
                                            <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />
                                            <div className="relative flex flex-col items-center gap-6 w-full">
                                                {/* Position Label */}
                                                {card.position && (
                                                    <div className="text-sm tracking-[0.2em] text-purple-200 font-bold font-['Hahmlet'] bg-purple-600/20 px-4 py-2 rounded-full border border-purple-400/30">
                                                        {card.position}
                                                    </div>
                                                )}
                                                <div className="text-xs tracking-[0.3em] text-purple-400/70 font-bold font-['Hahmlet'] uppercase bg-purple-500/10 px-3 py-1.5 rounded-full border border-purple-500/20">
                                                    {card.type}
                                                </div>
                                                <div className="relative w-32 h-48 rounded-lg overflow-hidden border-2 border-purple-500/20 shadow-md transform group-hover:-rotate-2 transition-transform duration-500">
                                                    <img src={card.img} alt={card.name} className={`w-full h-full object-cover scale-[1.12] ${card.isReversed ? 'rotate-180' : ''}`} />
                                                    <div className="absolute inset-0 border border-purple-400/20 pointer-events-none" />
                                                </div>
                                                <div className="text-center space-y-4 w-full">
                                                    <h4 className="text-xl font-bold font-['Hahmlet'] text-purple-200">{card.name}</h4>
                                                    <div className="text-[12px] text-purple-300 font-bold italic border-y border-purple-500/5 py-2">"{card.desc}"</div>
                                                    <p className="mt-4 text-[11px] font-bold text-purple-400/40 uppercase tracking-widest">
                                                        자세히 보기
                                                    </p>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </section>
                        </div>

                        {/* Mystical Symbol branding section */}
                        <div className="flex flex-col items-center mt-10 mb-4 w-full">
                            <div className="w-full max-w-xs h-[1px] bg-gradient-to-r from-transparent via-purple-500/10 to-transparent mb-8" />
                            <motion.div
                                initial={{ opacity: 0, scale: 1.2, rotate: -15 }}
                                whileInView={{ opacity: 0.6, scale: 1, rotate: 0 }}
                                viewport={{ once: true }}
                                transition={{ type: "spring", damping: 15 }}
                                className="relative"
                            >
                                <Sparkles size={96} className="text-purple-500/30" />
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
                        <Download size={22} className="text-purple-400" /> 이미지 저장하기
                    </button>

                    <button
                        onClick={onRestart}
                        className="w-full md:w-auto flex items-center justify-center gap-3 px-16 py-5 bg-purple-600 text-white hover:bg-purple-700 border border-purple-500/30 rounded-full transition-all font-bold text-lg shadow-xl"
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
                            className="relative w-full max-w-2xl bg-[#1a0f2e] rounded-[2rem] shadow-2xl overflow-hidden border-2 border-purple-500/30 font-['Hahmlet']"
                        >
                            {/* Cosmic texture */}
                            <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />

                            <button
                                onClick={() => setSelectedCard(null)}
                                className="absolute top-6 right-6 p-2 rounded-full hover:bg-purple-500/20 transition-colors z-20"
                            >
                                <X size={24} className="text-purple-300" />
                            </button>

                            <div className="relative z-10 p-8 md:p-12 flex flex-col md:flex-row gap-8 md:gap-12">
                                {/* Left: Card Image */}
                                <div className="w-full md:w-48 shrink-0 flex flex-col items-center gap-4">
                                    <div className="relative w-40 h-60 rounded-xl overflow-hidden border-4 border-purple-500/10 shadow-xl">
                                        <img src={selectedCard.img} alt={selectedCard.name} className={`w-full h-full object-cover scale-[1.15] ${selectedCard.isReversed ? 'rotate-180' : ''}`} />
                                        <div className="absolute inset-0 border border-purple-400/20 pointer-events-none" />
                                    </div>
                                    {selectedCard.position && (
                                        <div className="text-sm tracking-[0.2em] text-purple-200 font-bold font-['Hahmlet'] bg-purple-600/20 px-4 py-2 rounded-full border border-purple-400/30">
                                            {selectedCard.position}
                                        </div>
                                    )}
                                    <div className="text-xs font-bold text-purple-400/60 tracking-[0.3em] uppercase">
                                        {selectedCard.type}
                                    </div>
                                </div>

                                {/* Right: Card Text */}
                                <div className="flex-1 space-y-6">
                                    <div className="space-y-2">
                                        <h3 className="text-3xl font-bold text-purple-200">{selectedCard.name}</h3>
                                        <div className="text-lg text-purple-300 font-bold italic">"{selectedCard.desc}"</div>
                                    </div>

                                    <div className="w-full h-[1px] bg-gradient-to-r from-purple-500/20 to-transparent" />

                                    <div className="space-y-4">
                                        <p className="text-purple-300/90 text-base md:text-lg leading-[1.8] break-keep">
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

export default TarotResultView;
