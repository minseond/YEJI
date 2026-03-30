import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Heart, Coins, Briefcase, GraduationCap, Activity, Sparkles, ArrowUpDown } from 'lucide-react';
import type { UnseResultListItem } from '../../api/unse';

interface HistoryListUnseProps {
    data: UnseResultListItem[];
    isLoading: boolean;
    onSelect: (id: number) => void;
}

const CATEGORY_MAP: Record<string, string> = {
    'total': '종합운',
    'general': '종합운',
    'love': '연애운',
    'money': '재물운',
    'wealth': '재물운',
    'career': '직업운',
    'health': '건강운',
    'study': '학업운'
};

const getCategoryStyles = (category: string) => {
    const cat = category?.toLowerCase() || 'total';
    switch (cat) {
        case 'love':
            return { icon: Heart, bg: 'bg-rose-500/20', text: 'text-rose-400', border: 'border-rose-500/30' };
        case 'money':
        case 'wealth':
            return { icon: Coins, bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' };
        case 'career':
            return { icon: Briefcase, bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' };
        case 'health':
            return { icon: Activity, bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' };
        case 'study':
        case 'academic':
            return { icon: GraduationCap, bg: 'bg-violet-500/20', text: 'text-violet-400', border: 'border-violet-500/30' };
        case 'total':
        case 'general':
        default:
            return { icon: Sparkles, bg: 'bg-indigo-500/20', text: 'text-indigo-400', border: 'border-indigo-500/30' };
    }
};

const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}.${month}.${day}`;
};

const HistoryListUnse = ({ data, isLoading, onSelect }: HistoryListUnseProps) => {
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

    const uniqueCategories = useMemo(() => {
        if (!data) return [];
        const cats = new Set(data.map(item => item.category?.toLowerCase() || 'total'));
        return ['all', ...Array.from(cats)];
    }, [data]);

    const filteredAndSortedData = useMemo(() => {
        if (!data) return [];
        let result = [...data];

        if (selectedCategory !== 'all') {
            result = result.filter(item => (item.category?.toLowerCase() || 'total') === selectedCategory);
        }

        result.sort((a, b) => {
            const dateA = new Date(a.created_at).getTime();
            const dateB = new Date(b.created_at).getTime();
            return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });

        return result;
    }, [data, selectedCategory, sortOrder]);
    if (isLoading) {
        return <div className="text-white/50 text-center py-20 font-['Gowun_Batang']">운세 기록을 불러오는 중입니다...</div>;
    }

    if (!data || data.length === 0) {
        return (
            <div className="text-center py-20 space-y-2">
                <div className="text-white/30 font-light font-['Gowun_Batang']">저장된 운세 대화가 없습니다.</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Filter & Sort Controls */}
            {!isLoading && data && data.length > 0 && (
                <div className="flex flex-col gap-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex-1 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide flex items-center gap-2">
                            {uniqueCategories.map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setSelectedCategory(cat)}
                                    className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${selectedCategory === cat
                                        ? 'bg-amber-600 text-white border-amber-500 shadow-md'
                                        : 'bg-white/5 text-white/50 border-white/10 hover:bg-white/10'
                                        }`}
                                >
                                    {cat === 'all' ? '전체' : (CATEGORY_MAP[cat.toLowerCase()] || cat)}
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
            )}

            <div className="space-y-3">
                {filteredAndSortedData.map((item, index) => {
                    const styles = getCategoryStyles(item.category);
                    const CategoryIcon = styles.icon;
                    const categoryLabel = CATEGORY_MAP[item.category?.toLowerCase()] || item.category || '운세';
                    const formattedDate = formatDate(item.created_at);

                    return (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            onClick={() => onSelect(item.id)}
                            className="bg-black/40 border border-white/5 rounded-2xl p-4 flex items-center justify-between hover:bg-white/5 hover:border-amber-500/30 cursor-pointer transition-all group relative overflow-hidden"
                        >
                            {/* Hover Overlay */}
                            <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity bg-gradient-to-r ${styles.bg.replace('/20', '')} to-transparent`} />

                            <div className="flex items-center gap-5 relative z-10 w-full">
                                {/* Icon Box */}
                                <div className={`w-12 h-12 rounded-2xl ${styles.bg} flex items-center justify-center ${styles.text} border ${styles.border} group-hover:scale-110 transition-transform shadow-lg`}>
                                    <CategoryIcon size={24} strokeWidth={1.5} />
                                </div>

                                {/* Content */}
                                <div className="flex flex-col gap-1 flex-1">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full bg-white/5 border border-white/5 ${styles.text}`}>
                                            {categoryLabel}
                                        </span>
                                    </div>
                                    <h4 className="text-white/90 font-['Gowun_Batang'] text-lg font-bold line-clamp-1 group-hover:text-amber-200 transition-colors">
                                        {categoryLabel}의 흐름 분석
                                    </h4>
                                </div>

                                {/* Date - Moved to Right */}
                                <div className="text-base md:text-lg text-white/50 font-mono font-bold tracking-wider tabular-nums">
                                    {formattedDate}
                                </div>

                                {/* Chevron */}
                                <div className="text-white/20 group-hover:text-amber-500/70 transition-colors group-hover:translate-x-1 duration-300">
                                    <ChevronRight size={20} />
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

export default HistoryListUnse;
