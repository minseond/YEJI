import { useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, ChevronRight, Dices } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const EventPage = () => {
    const navigate = useNavigate();
    const [hoveredEvent, setHoveredEvent] = useState<number | null>(null);

    const events = [
        {
            id: 1,
            title: '매일매일 출석체크',
            description: '하루에 한 번, 무료 FP를 받아가세요.',
            icon: Calendar,
            color: 'from-blue-500 to-cyan-500',
            reward: '최대 100FP',
            status: '진행중'
        },
        {
            id: 2,
            title: '행운의 룰렛',
            description: '최대 500FP 당첨 기회!',
            icon: Dices,
            color: 'from-purple-500 to-pink-500',
            reward: '최대 500FP',
            status: '진행중'
        }
    ];

    return (
        <div className="h-screen pt-24 px-6 pb-12 w-full mx-auto font-['Pretendard'] overflow-y-auto custom-scrollbar relative">
            <div className="max-w-7xl mx-auto relative z-10">
                {/* Background Ambience */}
                <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/30 via-[#0b0d14] to-black pointer-events-none -z-10" />
                <div className="fixed top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none -z-10" />

                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-16 text-center space-y-4 relative"
                >
                    <div className="inline-block relative">
                        <h1 className="text-5xl md:text-7xl font-bold font-gmarket tracking-tight">
                            <span className="bg-gradient-to-r from-white via-indigo-200 to-indigo-400 text-transparent bg-clip-text drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]">
                                EVENTS
                            </span>
                        </h1>
                    </div>
                    <p className="text-indigo-200/60 text-lg font-light tracking-wide">
                        당신을 위해 준비한 특별한 이벤트를 놓치지 마세요.
                    </p>
                </motion.div>

                {/* Event Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {events.map((event, index) => (
                        <motion.div
                            key={event.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            onHoverStart={() => setHoveredEvent(event.id)}
                            onHoverEnd={() => setHoveredEvent(null)}
                            onClick={() => navigate(`/events/${event.id}`)}
                            className="group relative cursor-pointer min-h-[280px]"
                        >
                            {/* Card Glow Effect */}
                            <div className={`absolute -inset-0.5 bg-gradient-to-r ${event.color} rounded-[2rem] opacity-30 group-hover:opacity-100 blur transition-opacity duration-500`} />

                            {/* Main Card Content */}
                            <div className="relative h-full bg-[#0f111a] rounded-[2rem] border border-white/10 p-8 flex flex-col justify-between overflow-hidden group-hover:bg-[#13151f] transition-colors duration-300">

                                {/* Background Decorations */}
                                <div className={`absolute top-0 right-0 w-64 h-64 bg-gradient-to-br ${event.color} opacity-5 blur-[80px] rounded-full translate-x-1/2 -translate-y-1/2 group-hover:opacity-10 transition-opacity duration-500`} />
                                <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay" />

                                <div className="flex justify-between items-start relative z-10">
                                    <div className={`p-4 rounded-2xl bg-gradient-to-br ${event.color} bg-opacity-20 shadow-[0_8px_30px_rgb(0,0,0,0.12)] group-hover:scale-110 transition-transform duration-300 border border-white/10`}>
                                        <event.icon size={36} className="text-white drop-shadow-lg" />
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`px-4 py-1.5 rounded-full bg-gradient-to-r ${event.color} bg-opacity-10 border border-white/10 text-white font-bold text-sm shadow-inner`}>
                                            {event.reward}
                                        </span>
                                    </div>
                                </div>

                                <div className="space-y-3 relative z-10 mt-8">
                                    <h3 className="text-3xl font-bold text-white font-gmarket group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-indigo-300 transition-all duration-300">
                                        {event.title}
                                    </h3>
                                    <p className="text-white/50 text-base leading-relaxed group-hover:text-white/70 transition-colors">
                                        {event.description}
                                    </p>
                                </div>

                                <div className="mt-8 flex items-center justify-between relative z-10 border-t border-white/5 pt-6">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                        <span className="text-xs text-indigo-300/80 font-bold tracking-widest uppercase">
                                            {event.status}
                                        </span>
                                    </div>
                                    <motion.div
                                        animate={{ x: hoveredEvent === event.id ? 5 : 0 }}
                                        className={`w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/50 group-hover:text-white group-hover:bg-gradient-to-r ${event.color} group-hover:border-transparent transition-all shadow-lg`}
                                    >
                                        <ChevronRight size={20} />
                                    </motion.div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default EventPage;
