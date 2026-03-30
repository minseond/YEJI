import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Layers, ArrowUpDown } from 'lucide-react';
import type { CardResultDetailResponse } from '../../api/card';

interface HistoryListCardProps {
    data: CardResultDetailResponse[];
    isLoading: boolean;
    onSelect: (id: number) => void;
}

const CATEGORY_MAP: Record<string, string> = {
    'TARO': '타로',
    'HWATU': '화투'
};

const TOPIC_MAP: Record<string, string> = {
    'MONEY': '금전운',
    'WEALTH': '금전운',
    'LOVE': '연애운',
    'CAREER': '직업운',
    'HEALTH': '건강운',
    'STUDY': '학업운',
    'FAMILY': '가정운',
    'TOTAL': '종합운'
};

const HistoryListCard = ({ data, isLoading, onSelect }: HistoryListCardProps) => {
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

    const filteredAndSortedData = useMemo(() => {
        if (!data) return [];
        let result = [...data];

        if (selectedCategory !== 'all') {
            result = result.filter(item => item.category === selectedCategory);
        }

        result.sort((a, b) => {
            const dateA = new Date(a.createdAt).getTime();
            const dateB = new Date(b.createdAt).getTime();
            return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });

        return result;
    }, [data, selectedCategory, sortOrder]);

    if (isLoading) {
        return <div className="text-white/50 text-center py-20 font-gmarket">카드 점괘 기록을 불러오는 중입니다...</div>;
    }

    if (!data || data.length === 0) {
        return (
            <div className="text-center py-20 space-y-2">
                <div className="text-white/30 font-light font-gmarket">저장된 카드 점괘가 없습니다.</div>
            </div>
        );
    }

    return (
        <div className="space-y-6 font-gmarket">
            {/* Filter & Sort Controls */}
            <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex-1 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide flex items-center gap-2">
                        {['all', 'TARO', 'HWATU'].map(cat => (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${selectedCategory === cat
                                    ? 'bg-amber-600 text-white border-amber-500 shadow-md'
                                    : 'bg-white/5 text-white/50 border-white/10 hover:bg-white/10'
                                    }`}
                            >
                                {cat === 'all' ? '전체' : CATEGORY_MAP[cat]}
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={() => setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-bold text-white/70 transition-all whitespace-nowrap"
                    >
                        <ArrowUpDown size={14} />
                        <span>{sortOrder === 'desc' ? '최신순' : '과거순'}</span>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredAndSortedData.map((item, index) => (
                    <motion.div
                        key={item.cardResultId}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => onSelect(item.cardResultId)}
                        className="bg-black/40 border border-white/5 rounded-xl p-5 hover:bg-white/5 hover:border-purple-500/30 cursor-pointer transition-all group relative overflow-hidden"
                    >
                        <div className="relative z-10 flex flex-col h-full justify-between">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center border transition-colors
                                    ${item.category === 'TARO'
                                            ? 'bg-purple-900/20 border-purple-500/20 text-purple-400'
                                            : 'bg-amber-900/20 border-amber-500/20 text-amber-400'}`
                                    }>
                                        {item.category === 'TARO' ? <BookOpen size={18} /> : <Layers size={18} />}
                                    </div>
                                    <div>
                                        <div className="text-xs font-gmarket text-white/50 mb-0.5">
                                            {item.category === 'TARO' ? '타로 카드' : '화투 점괘'}
                                        </div>
                                        <div className="text-white/30 text-xs">
                                            {new Date(item.createdAt).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>

                                {item.score > 0 && (
                                    <div className="text-xs font-bold px-2 py-1 rounded-full bg-white/5 border border-white/10 text-amber-200">
                                        운세지수 {item.score}점
                                    </div>
                                )}
                            </div>

                            <div>
                                <h4 className="text-white font-gmarket text-lg mb-2 line-clamp-1 group-hover:text-purple-300 transition-colors">
                                    {TOPIC_MAP[item.question] || item.question || "질문 내용 없음"}
                                </h4>
                                {item.cards && item.cards.length > 0 && (
                                    <div className="flex gap-1 mt-2 opacity-50">
                                        {/* Small visual indicators for cards */}
                                        {item.cards.slice(0, 3).map((_, i) => (
                                            <div key={i} className={`w-6 h-8 rounded-sm border ${item.category === 'TARO' ? 'bg-purple-900/40 border-purple-500/30' : 'bg-red-900/40 border-red-500/30'}`} />
                                        ))}
                                        {item.cards.length > 3 && <span className="text-xs text-white/20 self-end">...</span>}
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default HistoryListCard;
