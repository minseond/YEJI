import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';

// API
import api from '../../api/axios';
import { getSajuHistory } from '../../api/saju';
import { getUnseHistory } from '../../api/unse';
import { getCardHistoryList } from '../../api/card';
import { getCompatibilityHistory } from '../../api/compatibility';

// Components
import HistoryListSaju from '../history/HistoryListSaju';
import HistoryListUnse from '../history/HistoryListUnse';
import HistoryListCard from '../history/HistoryListCard';
import HistoryListCompatibility from '../history/HistoryListCompatibility';

// Type Definitions
type TabType = 'integrated' | 'fortune' | 'card' | 'compatibility';

const History = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [activeTab, setActiveTab] = useState<TabType>((location.state as any)?.tab || 'integrated');
    const [data, setData] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch Data on Tab Change
    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setData(null);
            try {
                let result;
                switch (activeTab) {
                    case 'integrated':
                        // Fetch Saju history
                        const sajuResult = await getSajuHistory();

                        // Fetch user info separately since backend doesn't include it
                        try {
                            const token = localStorage.getItem('accessToken');
                            if (!token) throw new Error('No accessToken found');

                            const decoded: any = jwtDecode(token);
                            const userId = decoded.userId;
                            if (!userId) throw new Error('No userId found in token');

                            const userInfoResponse = await api.get(`/user/${userId}`);
                            // Flexible unwrapping: try data.data (ApiResponse) then data (Plain response)
                            const userData = userInfoResponse.data.data || userInfoResponse.data;

                            if (!userData || typeof userData !== 'object') {
                                throw new Error('Invalid user data received');
                            }

                            // Robust Date Parsing (Handles string "YYYY-MM-DD" or array [YYYY, MM, DD])
                            let birthDate: Date | null = null;
                            if (userData.birthDate) {
                                if (Array.isArray(userData.birthDate)) {
                                    const [y, m, d] = userData.birthDate;
                                    birthDate = new Date(y, m - 1, d);
                                } else {
                                    birthDate = new Date(userData.birthDate);
                                }
                            }

                            // Combine user info with Saju result
                            result = {
                                ...sajuResult,
                                user_info: {
                                    name: userData.nameKor || userData.nickname || '사용자',
                                    gender: userData.gender || 'M',
                                    birth_year: birthDate?.getFullYear() || 0,
                                    birth_month: birthDate ? birthDate.getMonth() + 1 : 0,
                                    birth_day: birthDate?.getDate() || 0,
                                    birth_time: userData.birthTime || '00:00:00',
                                    calendar_type: userData.isSolar ? 'solar' : 'lunar'
                                }
                            };
                        } catch (userError) {
                            console.error('[History] Failed to fetch user info:', userError);
                            result = sajuResult; // Fallback
                        }
                        break;
                    case 'fortune':
                        result = await getUnseHistory();
                        break;
                    case 'card':
                        result = await getCardHistoryList();
                        break;
                    case 'compatibility':
                        result = await getCompatibilityHistory();
                        break;
                }
                setData(result);
            } catch (error) {
                console.error("Failed to fetch history:", error);
                // Handle error state if needed
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [activeTab]);

    const handleBack = () => {
        navigate('/');
    };

    const handleSelectResult = (id: number) => {
        // Navigate to detail pages based on category
        switch (activeTab) {
            case 'integrated':
                navigate('/history/saju');
                break;
            case 'fortune':
                navigate(`/unse/result/${id}`); // Need to ensure route exists
                break;
            case 'card':
                navigate(`/cards/result/${id}`); // Need to ensure route exists
                break;
            case 'compatibility':
                navigate(`/compatibility/result/${id}`); // Need to ensure route exists
                break;
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`h-screen w-full relative overflow-y-auto custom-scrollbar font-sans transition-colors duration-700 bg-[#1c1410] text-amber-50`}
        >
            {/* Background Texture Overlay */}
            <div className={`fixed inset-0 pointer-events-none opacity-20 bg-[url("/textures/hanji_pattern.png")] mix-blend-overlay`} />

            {/* Nav */}
            <div className="absolute top-6 left-6 z-50">
                <button
                    onClick={handleBack}
                    className="flex items-center gap-2 text-white/50 hover:text-white transition-colors px-4 py-2 rounded-full bg-black/20 hover:bg-black/40 backdrop-blur-md"
                >
                    <ArrowLeft size={18} />
                    <span className="font-['Gowun_Batang'] text-sm">돌아가기</span>
                </button>
            </div>

            <div className="container mx-auto px-4 pt-24 pb-20 max-w-4xl relative z-10">

                {/* Tab Navigation */}
                <div className="flex justify-center mb-12 overflow-x-auto py-2">
                    <div className="relative inline-flex gap-1 p-1 bg-gradient-to-b from-amber-950/40 to-stone-950/60 rounded-2xl backdrop-blur-md border border-amber-900/20 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
                        {/* Animated Background Indicator */}
                        <motion.div
                            layoutId="activeTabIndicator"
                            className="absolute inset-y-1 rounded-xl bg-gradient-to-br from-amber-600/90 to-amber-800/90 shadow-[0_4px_20px_rgba(217,119,6,0.3)] border border-amber-500/30"
                            initial={false}
                            animate={{
                                left: activeTab === 'integrated' ? '4px' :
                                    activeTab === 'fortune' ? 'calc(25% + 2px)' :
                                        activeTab === 'card' ? 'calc(50% + 2px)' :
                                            'calc(75% + 0px)',
                                width: 'calc(25% - 4px)'
                            }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        />

                        {[
                            { id: 'integrated', label: '통합사주' },
                            { id: 'fortune', label: '운세' },
                            { id: 'card', label: '카드점괘' },
                            { id: 'compatibility', label: '궁합' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as TabType)}
                                className={`relative z-10 px-6 md:px-8 py-3 rounded-xl text-sm font-bold transition-all duration-300 min-w-[90px] md:min-w-[110px]
                                    ${activeTab === tab.id
                                        ? 'text-white shadow-lg'
                                        : 'text-amber-200/50 hover:text-amber-100/80'}
                                `}
                            >
                                <span className="font-['JoseonPalace'] tracking-wide">
                                    {tab.label}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content Area */}
                <div className="min-h-[400px]">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -10 }}
                            transition={{ duration: 0.3 }}
                        >
                            {activeTab === 'integrated' && (
                                <HistoryListSaju data={data} isLoading={isLoading} />
                            )}
                            {activeTab === 'fortune' && (
                                <HistoryListUnse data={data} isLoading={isLoading} onSelect={handleSelectResult} />
                            )}
                            {activeTab === 'card' && (
                                <HistoryListCard data={data} isLoading={isLoading} onSelect={handleSelectResult} />
                            )}
                            {activeTab === 'compatibility' && (
                                <HistoryListCompatibility data={data} isLoading={isLoading} onSelect={handleSelectResult} />
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>

            </div>
        </motion.div >
    );
};

export default History;
