import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';
import { getCompatibilityDetail, type CompatibilityResponse } from '../../api/compatibility';
import CompatibilityResultView from '../results/CompatibilityResultView';
import ParticleBackground from '../effects/ParticleBackground';

const CompatibilityHistoryDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [historyData, setHistoryData] = useState<CompatibilityResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            if (!id) return;
            try {
                const response = await getCompatibilityDetail(Number(id));
                if (response) {
                    setHistoryData(response);
                }
            } catch (error) {
                console.error('Failed to fetch compatibility detail:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [id]);

    const handleBack = () => {
        navigate('/history', { state: { tab: 'compatibility' } });
    };

    if (loading) {
        return (
            <div className="w-full h-screen bg-[#1c1410] flex items-center justify-center text-amber-500/50 font-['Gowun_Batang']">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
                    <span>궁합 결과를 불러오고 있습니다...</span>
                </div>
            </div>
        );
    }

    if (!historyData) {
        return (
            <div className="w-full h-screen bg-[#1c1410] flex flex-col items-center justify-center text-amber-200 gap-6">
                <p className="font-['Gowun_Batang'] text-lg">기록을 찾을 수 없습니다.</p>
                <button
                    onClick={handleBack}
                    className="px-8 py-3 bg-amber-900/40 text-amber-200 border border-amber-500/30 rounded-full hover:bg-amber-800/60 transition-all"
                >
                    히스토리로 돌아가기
                </button>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-[#1c1410] text-amber-50 overflow-hidden"
        >
            {/* Background Layers matching CompatibilityPage */}
            <div
                className="fixed inset-0 bg-cover bg-center bg-no-repeat transition-all duration-1000 scale-105"
                style={{ backgroundImage: "url('/backgrounds/todayfortune.png')" }}
            />
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
            <div className="fixed inset-0 pointer-events-none opacity-20 bg-[url('/textures/hanji_pattern.png')] mix-blend-overlay" />

            <div className="relative z-10 w-full h-full flex flex-col items-center overflow-y-auto scrollbar-hide">
                {/* Particles */}
                <div className="fixed inset-0 pointer-events-none">
                    <ParticleBackground type="eastern" opacity={0.2} />
                </div>

                {/* Header/Exit Button */}
                <div className="fixed top-8 right-8 z-[100]">
                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleBack}
                        className="flex items-center gap-2 px-6 py-2 rounded-full border bg-amber-600/20 border-amber-500/30 text-amber-100 hover:bg-amber-600/40 shadow-xl backdrop-blur-md transition-all group pointer-events-auto"
                    >
                        <span className="font-bold font-['Gowun_Batang'] tracking-wider">목록으로</span>
                        <ArrowLeft size={20} className="rotate-180 group-hover:translate-x-1 transition-transform" />
                    </motion.button>
                </div>

                {/* Score Report View */}
                <CompatibilityResultView
                    data={historyData}
                    onBack={handleBack}
                    onExit={handleBack}
                />
            </div>
        </motion.div>
    );
};

export default CompatibilityHistoryDetail;
