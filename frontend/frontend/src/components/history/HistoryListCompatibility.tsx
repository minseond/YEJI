import { motion } from 'framer-motion';
import { User, ChevronRight } from 'lucide-react';
import type { CompatibilityResponse } from '../../api/compatibility'; // Need to export this interface from api/compatibility.ts

interface HistoryListCompatibilityProps {
    data: CompatibilityResponse[];
    isLoading: boolean;
    onSelect: (id: number) => void;
}

const HistoryListCompatibility = ({ data, isLoading, onSelect }: HistoryListCompatibilityProps) => {
    if (isLoading) {
        return <div className="text-white/50 text-center py-20 font-['Gowun_Batang']">궁합 분석 기록을 불러오는 중입니다...</div>;
    }

    const list = Array.isArray(data) ? data : [];

    if (list.length === 0) {
        return (
            <div className="text-center py-20 space-y-2">
                <div className="text-white/30 font-light font-['Gowun_Batang']">저장된 궁합 결과가 없습니다.</div>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {list.map((item, index) => (
                <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => onSelect(item.id)}
                    className="bg-black/40 border border-pink-500/10 rounded-xl p-4 flex items-center justify-between hover:bg-pink-900/10 hover:border-pink-500/30 cursor-pointer transition-all group"
                >
                    <div className="flex items-center gap-5">
                        <div className="relative">
                            <div className="w-12 h-12 rounded-full bg-pink-900/20 flex items-center justify-center text-pink-400 border border-pink-500/20">
                                <User size={20} className="opacity-70" />
                            </div>
                            {item.resultData?.score?.total && (
                                <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-black border border-white/10 flex items-center justify-center text-[10px] font-bold text-white shadow-lg">
                                    {item.resultData.score.total}
                                </div>
                            )}
                        </div>
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs text-white/30">
                                    {new Date(item.createdAt).toLocaleDateString()}
                                </span>
                            </div>
                            <h4 className="text-pink-100 font-['JoseonPalace'] text-lg font-bold group-hover:text-pink-300 transition-colors flex items-center gap-2">
                                <User size={14} className="opacity-50" />
                                {item.targetName}
                            </h4>
                        </div>
                    </div>

                    <div className="text-white/20 group-hover:text-pink-400 transition-colors">
                        <ChevronRight size={20} />
                    </div>
                </motion.div>
            ))
            }
        </div >
    );
};

export default HistoryListCompatibility;
