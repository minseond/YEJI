import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Calendar, Dices, Hammer, Clock, Gift } from 'lucide-react';

const EventDetailPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    // Mock Data (Shared with EventPage)
    // In a real app, this would come from a store or API
    const events = [
        {
            id: 1,
            title: '매일매일 출석체크',
            description: '하루에 한 번, 포츈 포인트를 모으세요.',
            fullDescription: '매일 접속하여 출석체크를 완료하면 포츈 포인트(FP)를 드립니다.\n획득한 FP로 다양한 운세 콘텐츠를 즐겨보세요!\n매일 자정(00:00)에 출석 기회가 초기화되니 놓치지 마세요.',
            icon: Calendar,
            color: 'from-blue-500 to-cyan-500',
            reward: '10 ~ 100 FP',
            period: '상시 진행',
            status: '진행중'
        },
        {
            id: 2,
            title: '행운의 룰렛',
            description: '당신의 운을 시험해 보세요! 최대 10,000 FP 당첨 기회!',
            fullDescription: '매일 한 번의 무료 기회가 주어집니다.\n당신의 운을 시험해 보세요.\n과연 오늘의 행운은 당신의 편일까요?',
            icon: Dices,
            color: 'from-purple-500 to-pink-500',
            reward: 'Random FP',
            period: '2026.01.01 ~ 2026.12.31',
            status: '진행중'
        }
    ];

    const event = events.find(e => e.id === Number(id));

    if (!event) {
        return (
            <div className="min-h-screen flex items-center justify-center text-white/50">
                <p>이벤트를 찾을 수 없습니다.</p>
                <button onClick={() => navigate('/events')} className="ml-4 underline hover:text-white">돌아가기</button>
            </div>
        );
    }

    return (
        <div className="h-screen pt-24 px-6 pb-20 w-full mx-auto font-['Pretendard'] overflow-y-auto custom-scrollbar relative">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="mb-8"
                >
                    <button
                        onClick={() => navigate('/events')}
                        className="flex items-center gap-2 text-white/60 hover:text-white transition-colors mb-6"
                    >
                        <ArrowLeft size={20} />
                        <span>목록으로 돌아가기</span>
                    </button>

                    <div className="flex items-start justify-between gap-6">
                        <div>
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.2 }}
                                className="inline-block px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-bold tracking-wider mb-3 border border-indigo-500/30"
                            >
                                {event.status}
                            </motion.span>
                            <motion.h1
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="text-3xl md:text-5xl font-bold text-white font-gmarket leading-tight"
                            >
                                {event.title}
                            </motion.h1>
                        </div>
                        {/* Development Badge */}
                        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-md h-fit mt-2">
                            <Hammer size={12} className="text-amber-500/80" />
                            <span className="text-amber-200/60 text-[10px] font-bold tracking-wider">개발 중</span>
                        </div>
                    </div>
                </motion.div>

                {/* Content Body */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="space-y-6"
                >
                    {/* Main Banner / Icon Area */}
                    <div className="w-full aspect-video md:aspect-[21/9] rounded-3xl bg-white/5 border border-white/10 overflow-hidden relative flex items-center justify-center">
                        <div className={`absolute inset-0 bg-gradient-to-br ${event.color} opacity-20`} />
                        <div className={`absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] ${event.color} opacity-10 blur-3xl`} />

                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.4, type: "spring" }}
                            className={`p-12 rounded-full bg-gradient-to-br ${event.color} shadow-[0_0_50px_rgba(0,0,0,0.5)] z-10`}
                        >
                            <event.icon size={64} className="text-white drop-shadow-xl" />
                        </motion.div>
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Description */}
                        <div className="md:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-8 backdrop-blur-sm">
                            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                                <span>이벤트 안내</span>
                            </h3>
                            <p className="text-white/70 leading-relaxed whitespace-pre-line">
                                {event.fullDescription}
                            </p>
                        </div>

                        {/* Metadata Side Panel */}
                        <div className="space-y-4">
                            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                                <h4 className="text-sm text-white/40 font-bold mb-4 uppercase tracking-widest">Information</h4>

                                <div className="space-y-4">
                                    <div className="flex items-start gap-3">
                                        <Clock size={16} className="text-indigo-400 mt-0.5" />
                                        <div>
                                            <p className="text-xs text-white/40 mb-0.5">기간</p>
                                            <p className="text-sm text-white/90 font-medium">{event.period || '상시 진행'}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <Gift size={16} className="text-amber-400 mt-0.5" />
                                        <div>
                                            <p className="text-xs text-white/40 mb-0.5">보상</p>
                                            <p className="text-sm text-amber-200 font-bold">{event.reward}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <button
                                className="w-full py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-lg hover:shadow-indigo-500/25 flex items-center justify-center gap-2"
                                onClick={() => alert('이벤트 참여 기능은 준비 중입니다.')}
                            >
                                <event.icon size={18} />
                                이벤트 참여하기
                            </button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default EventDetailPage;
