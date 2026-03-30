import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { UserPlus, Search, Users, Heart, Bell, Sparkles } from 'lucide-react';
import {
    getMyFriends,
    getPendingRequests,
    searchFriends,
    sendFriendRequest,
    handleFriendRequest,
    deleteFriend,
    type Friend
} from '../../api/friend';
import Modal from '../common/Modal';
import { useSound } from '../../hooks/useSound';
import { useCharacterSettings, getSDCharacterImage } from '../../utils/character';

const FriendsPage = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [addFriendQuery, setAddFriendQuery] = useState('');
    const [searchResultState, setSearchResultState] = useState<'idle' | 'searching' | 'found' | 'not_found'>('idle');
    const { play } = useSound();
    const charSettings = useCharacterSettings();

    // API State
    const [friends, setFriends] = useState<Friend[]>([]);
    const [pendingRequests, setPendingRequests] = useState<Friend[]>([]);
    const [searchResults, setSearchResults] = useState<Friend[]>([]);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState<string | null>(null); // Track which action is loading

    // Modal State
    const [modalConfig, setModalConfig] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        type: 'info' | 'error' | 'success';
        redirect?: string;
        showCancel?: boolean;
        onConfirm?: () => void;
        confirmText?: string;
        cancelText?: string;
    }>({
        isOpen: false,
        title: '',
        message: '',
        type: 'info'
    });

    const closeModal = () => {
        setModalConfig(prev => ({ ...prev, isOpen: false }));
        if (modalConfig.redirect) {
            navigate(modalConfig.redirect);
        }
    };

    // Load friends and pending requests on mount
    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            setModalConfig({
                isOpen: true,
                title: '로그인 필요',
                message: '로그인이 필요한 서비스입니다.',
                type: 'error',
                redirect: '/'
            });
            return;
        }

        const loadData = async () => {
            try {
                await loadFriends();
            } catch (err) {
                console.error('Initial load failed:', err);
            }

            try {
                await loadPendingRequests();
            } catch (err) {
                console.error('Initial pending requests load failed:', err);
            }
        };

        loadData();
    }, []);

    const loadFriends = async () => {
        try {
            setLoading(true);
            const data = await getMyFriends();
            setFriends(data);
        } catch (err: any) {
            console.error('Failed to load friends:', err);
            setFriends([]); // Set empty array on error
        } finally {
            setLoading(false);
        }
    };

    const loadPendingRequests = async () => {
        try {
            const data = await getPendingRequests();
            setPendingRequests(data);
        } catch (err: any) {
            console.error('Failed to load pending requests:', err);
            setPendingRequests([]); // Set empty array on error
        }
    };

    const handleSearch = async () => {
        if (!addFriendQuery.trim()) return;
        play('SFX', 'SEAL_CLICK'); // Click Sound

        try {
            setActionLoading('search');
            setSearchResultState('searching');
            const results = await searchFriends(addFriendQuery);
            // Frontend Filtering: Exact Match Only
            const exactMatches = results.filter(user => user.nickname === addFriendQuery);
            setSearchResults(exactMatches);

            if (exactMatches.length === 0) {
                setSearchResultState('not_found');
            } else {
                setSearchResultState('found');
            }
        } catch (err: any) {
            console.error('Search failed:', err);
            setSearchResultState('not_found');
        } finally {
            setActionLoading(null);
        }
    };

    const handleSendRequest = async (userId: number) => {
        try {
            setActionLoading(`request-${userId}`);
            await sendFriendRequest(userId);
            setModalConfig({
                isOpen: true,
                title: '요청 완료',
                message: '친구 요청을 보냈습니다!',
                type: 'success'
            });
            setSearchResults([]); // Optional: Clear results or show sent status
            setSearchResultState('idle'); // Reset search state
            setAddFriendQuery(''); // Clear input
        } catch (err: any) {
            console.error('Failed to send request:', err);
            const errorMsg = err.response?.data?.message || '친구 요청에 실패했습니다.';
            setModalConfig({
                isOpen: true,
                title: '요청 실패',
                message: errorMsg,
                type: 'error'
            });
        } finally {
            setActionLoading(null);
        }
    };

    const handleAcceptRequest = async (friendshipId: number) => {
        if (!friendshipId) {
            console.error('friendshipId is missing!');
            return;
        }

        try {
            setActionLoading(`accept-${friendshipId}`);
            await handleFriendRequest(friendshipId, true);
            setModalConfig({
                isOpen: true,
                title: '친구 수락',
                message: '친구 요청을 수락했습니다!',
                type: 'success'
            });
            await Promise.all([loadFriends(), loadPendingRequests()]);
        } catch (err: any) {
            console.error('Failed to accept request:', err);
            const errorMsg = err.response?.data?.message || '요청 처리에 실패했습니다.';
            setModalConfig({
                isOpen: true,
                title: '오류 발생',
                message: errorMsg,
                type: 'error'
            });
        } finally {
            setActionLoading(null);
        }
    };

    const handleRejectRequest = async (friendshipId: number) => {
        if (!friendshipId) return;

        try {
            setActionLoading(`reject-${friendshipId}`);
            await handleFriendRequest(friendshipId, false);
            setModalConfig({
                isOpen: true,
                title: '거절 완료',
                message: '친구 요청을 거절했습니다.',
                type: 'info'
            });
            await loadPendingRequests();
        } catch (err: any) {
            console.error('Failed to reject request:', err);
            const errorMsg = err.response?.data?.message || '요청 처리에 실패했습니다.';
            setModalConfig({
                isOpen: true,
                title: '오류 발생',
                message: errorMsg,
                type: 'error'
            });
        } finally {
            setActionLoading(null);
        }
    };

    const handleDeleteFriend = async (userId: number) => {
        setModalConfig({
            isOpen: true,
            title: '친구 삭제',
            message: '정말 친구를 삭제하시겠습니까?',
            type: 'error',
            showCancel: true,
            confirmText: '삭제',
            cancelText: '취소',
            onConfirm: async () => {
                try {
                    setActionLoading(`delete-${userId}`);
                    await deleteFriend(userId);
                    setModalConfig(prev => ({ ...prev, isOpen: false })); // Close confirm modal
                    // Show success modal (need slight delay or separate state ideally, but simpler here)
                    setTimeout(() => {
                        setModalConfig({
                            isOpen: true,
                            title: '삭제 완료',
                            message: '친구가 삭제되었습니다.',
                            type: 'success'
                        });
                    }, 100);
                    await loadFriends();
                } catch (err: any) {
                    console.error('Failed to delete friend:', err);
                    const errorMsg = err.response?.data?.message || '친구 삭제에 실패했습니다.';
                    setModalConfig({
                        isOpen: true,
                        title: '삭제 실패',
                        message: errorMsg,
                        type: 'error'
                    });
                } finally {
                    setActionLoading(null);
                }
            }
        });
    };

    const stats = {
        total: friends.length,
        requests: pendingRequests.length
    };

    return (
        <div className="h-screen w-full bg-[#0b0d14] text-white overflow-hidden relative font-['GmarketSansMedium']">
            {/* Modern Background Effects */}
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_0%,_#1e1b4b_0%,_#0b0d14_100%)] pointer-events-none" />
            <div className="fixed top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-600/10 blur-[130px] rounded-full pointer-events-none" />
            <div className="fixed bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[130px] rounded-full pointer-events-none" />

            <Modal
                isOpen={modalConfig.isOpen}
                onClose={closeModal}
                title={modalConfig.title}
                message={modalConfig.message}
                type={modalConfig.type}
                showCancel={modalConfig.showCancel}
                onConfirm={modalConfig.onConfirm}
                confirmText={modalConfig.confirmText}
                cancelText={modalConfig.cancelText}
            />

            <div className="relative z-10 h-full w-full max-w-[1600px] mx-auto flex flex-col pt-24 px-8 pb-8">
                {/* Header */}
                <header className="flex flex-col md:flex-row items-start md:items-end justify-between mb-10 pb-6 border-b border-white/5">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-200 to-indigo-400 drop-shadow-[0_0_15px_rgba(99,102,241,0.3)]">
                            FRIENDS
                        </h1>
                        <p className="text-white/40 text-lg font-light mt-2 tracking-wide uppercase">
                            Connect with your destiny
                        </p>
                    </div>
                </header>

                {/* Main Content Layout */}
                <div className="flex-1 flex gap-8 overflow-hidden">
                    {/* Left Sidebar - Modern Glass Style */}
                    <aside className="w-72 shrink-0 flex flex-col gap-4">
                        <nav className="space-y-2">
                            {[
                                { id: 'all', label: '모든 친구', icon: Users },
                                { id: 'requests', label: '받은 요청', icon: Bell },
                                { id: 'find_friends', label: '친구 찾기', icon: UserPlus },
                                { id: 'compatibility', label: '궁합 보기', icon: Heart }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onMouseEnter={() => play('SFX', 'BRUSH_HOVER')}
                                    onClick={() => {
                                        setActiveTab(tab.id);
                                        play('SFX', 'BUTTON_SELECT');
                                    }}
                                    className={`w-full px-6 py-4 rounded-2xl transition-all duration-300 flex items-center justify-between group relative overflow-hidden border
                                    ${activeTab === tab.id
                                            ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300 font-bold shadow-[0_0_20px_rgba(99,102,241,0.2)]'
                                            : 'bg-white/5 border-transparent text-white/50 hover:text-white hover:bg-white/10 hover:border-white/10'
                                        }
                                `}
                                >
                                    <div className="flex items-center gap-4 relative z-10">
                                        <tab.icon size={20} className={activeTab === tab.id ? 'text-indigo-400' : 'text-white/30 group-hover:text-white/60'} />
                                        <span className="text-base tracking-widest">{tab.label}</span>
                                    </div>

                                    {tab.id === 'requests' && pendingRequests.length > 0 && (
                                        <span className="relative z-10 bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-lg">
                                            {pendingRequests.length}
                                        </span>
                                    )}

                                    {activeTab === tab.id && (
                                        <motion.div layoutId="activeTabGlow" className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-indigo-500 rounded-full blur-[2px]" />
                                    )}
                                </button>
                            ))}
                        </nav>
                    </aside>

                    {/* Center Content - Modern Glass Style */}
                    <main className="flex-1 bg-white/[0.03] border border-white/10 rounded-3xl p-8 overflow-hidden flex flex-col backdrop-blur-xl relative">
                        {/* Toolbar - Only visible in 'all' tab */}
                        {activeTab === 'all' && (
                            <div className="flex items-center justify-between mb-8 shrink-0">
                                <div className="relative w-96">
                                    <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                                    <input
                                        type="text"
                                        placeholder=""
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full h-12 pl-14 pr-4 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500/50 transition-all placeholder:text-white/20"
                                    />
                                </div>

                                <div className="flex items-center gap-3 px-6 py-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-300">
                                    <Users size={18} className="opacity-60" />
                                    <span className="text-base font-bold tracking-widest">
                                        친구 <span className="text-white px-1">{stats.total}</span>명
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Content Component */}
                        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 min-h-0">
                            <AnimatePresence mode="wait">
                                {activeTab === 'requests' ? (
                                    <motion.div
                                        key="requests"
                                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
                                        className={`${pendingRequests.length > 0 ? 'grid grid-cols-1 gap-4' : 'h-full'}`}
                                    >
                                        {pendingRequests.length === 0 ? (
                                            <div className="flex flex-col items-center justify-center h-full text-white/20 gap-4">
                                                <Bell size={48} className="opacity-10" />
                                                <p>받은 친구 요청이 없습니다.</p>
                                            </div>
                                        ) : (
                                            pendingRequests.map((req) => (
                                                <div key={req.userId} className="flex items-center justify-between p-6 rounded-2xl bg-white/5 border border-white/5 hover:border-indigo-500/30 transition-all group/card relative overflow-hidden">
                                                    <div className="flex items-center gap-5 relative z-10">
                                                        <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 shadow-lg flex items-center justify-center text-2xl font-bold border border-white/10 text-white">
                                                            {req.nickname[0]}
                                                        </div>
                                                        <div>
                                                            <h3 className="text-lg font-bold text-white">{req.nickname}</h3>
                                                            <p className="text-indigo-300/50 text-sm">새로운 친구 요청이 도착했습니다</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-3 relative z-10">
                                                        <button
                                                            onClick={() => handleAcceptRequest(req.friendshipId!)}
                                                            disabled={actionLoading === `accept-${req.friendshipId}`}
                                                            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all disabled:opacity-50 flex items-center gap-2 shadow-lg shadow-indigo-900/40"
                                                        >
                                                            {actionLoading === `accept-${req.friendshipId}` && (
                                                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                            )}
                                                            <span>수락</span>
                                                        </button>
                                                        <button
                                                            onClick={() => handleRejectRequest(req.friendshipId!)}
                                                            disabled={actionLoading === `reject-${req.friendshipId}`}
                                                            className="px-6 py-2.5 rounded-xl bg-white/5 hover:bg-red-500/10 text-white/40 hover:text-red-400 border border-white/5 hover:border-red-500/30 transition-all disabled:opacity-50"
                                                        >
                                                            거절
                                                        </button>
                                                    </div>
                                                </div>
                                            ))
                                        )}
                                    </motion.div>
                                ) : activeTab === 'find_friends' ? (
                                    <motion.div
                                        key="find_friends"
                                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
                                        className="max-w-2xl mx-auto py-12 w-full min-h-full flex flex-col justify-center"
                                    >
                                        <div className="relative mb-12">
                                            <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-indigo-400/40" size={24} />
                                            <input
                                                type="text"
                                                placeholder="친구의 이름/닉네임을 검색하세요"
                                                value={addFriendQuery}
                                                onChange={(e) => setAddFriendQuery(e.target.value)}
                                                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                                className="w-full h-16 pl-16 pr-24 bg-white/5 border border-white/10 rounded-2xl text-xl text-white placeholder:text-white/10 focus:outline-none focus:border-indigo-500/50 transition-all shadow-2xl"
                                            />
                                            <button
                                                onClick={handleSearch}
                                                disabled={!addFriendQuery.trim() || actionLoading === 'search'}
                                                className="absolute right-3 top-3 bottom-3 px-6 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold transition-all disabled:opacity-50 shadow-lg"
                                            >
                                                {actionLoading === 'search' ? (
                                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                ) : "검색"}
                                            </button>
                                        </div>

                                        {/* Search Results Area */}
                                        <div className="min-h-[200px]">
                                            {searchResultState === 'not_found' && (
                                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-10 text-white/30 gap-3">
                                                    <Search size={40} className="opacity-10" />
                                                    <p className="font-medium text-lg">해당하는 친구를 찾지 못했습니다.</p>
                                                </motion.div>
                                            )}

                                            {searchResultState === 'found' && searchResults.map((user) => (
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.95 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    className="bg-white/5 border border-white/10 rounded-2xl p-6 flex items-center justify-between shadow-2xl hover:border-indigo-500/30 transition-all"
                                                    key={user.userId}
                                                >
                                                    <div className="flex items-center gap-5">
                                                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center text-2xl font-bold border border-white/10 text-white">
                                                            {user.nickname[0]}
                                                        </div>
                                                        <div>
                                                            <h3 className="text-xl font-bold text-white">{user.nickname}</h3>
                                                            <p className="text-indigo-300/50 text-sm">함께하실 준비가 되었나요?</p>
                                                        </div>
                                                    </div>

                                                    <button
                                                        onClick={() => handleSendRequest(user.userId)}
                                                        disabled={actionLoading === `request-${user.userId}`}
                                                        className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all disabled:opacity-50 flex items-center gap-2 shadow-lg"
                                                    >
                                                        {actionLoading === `request-${user.userId}` ? (
                                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                        ) : (
                                                            <>
                                                                <UserPlus size={18} />
                                                                <span>친구 추가</span>
                                                            </>
                                                        )}
                                                    </button>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                ) : activeTab === 'compatibility' ? (
                                    <motion.div
                                        key="compatibility"
                                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
                                        className={`h-full ${friends.length > 0 ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : ''}`}
                                    >
                                        {friends.length === 0 ? (
                                            <div className="col-span-full flex flex-col items-center justify-center h-full text-white/20 gap-4">
                                                <Heart size={48} className="opacity-10" />
                                                <p>궁합을 확인할 친구가 없습니다.</p>
                                            </div>
                                        ) : (
                                            friends.map((friend) => (
                                                <motion.div
                                                    key={friend.userId}
                                                    whileHover={{ y: -5 }}
                                                    className="group bg-white/5 border border-white/10 hover:border-indigo-500/40 rounded-3xl p-8 transition-all flex flex-col items-center shadow-lg"
                                                >
                                                    <div className="relative mb-6">
                                                        <div className="absolute -inset-4 rounded-full border border-indigo-500/20 border-dashed animate-[spin_20s_linear_infinite] opacity-0 group-hover:opacity-100 transition-opacity" />
                                                        <div className="relative w-28 h-28 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 shadow-2xl flex items-center justify-center text-4xl font-bold border-4 border-white/5 text-white">
                                                            {friend.nickname[0]}
                                                        </div>
                                                    </div>
                                                    <h3 className="text-2xl font-bold text-white mb-6 group-hover:text-indigo-300 transition-colors">{friend.nickname}</h3>

                                                    <button
                                                        onClick={() => {
                                                            play('SFX', 'SEAL_CLICK');
                                                            navigate('/compatibility', { state: { selectedFriend: friend } });
                                                        }}
                                                        className="w-full py-3 bg-indigo-600/10 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 hover:border-indigo-500 rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg active:scale-95"
                                                    >
                                                        <Sparkles size={16} />
                                                        <span>궁합보기</span>
                                                    </button>
                                                </motion.div>
                                            ))
                                        )}
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="grid"
                                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                        className={`${friends.length > 0 ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'h-full'}`}
                                    >
                                        {loading ? (
                                            <div className="col-span-full flex flex-col items-center justify-center py-32 text-indigo-400/40 gap-6">
                                                <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
                                                <p className="tracking-widest animate-pulse uppercase font-light">Loading Destiny...</p>
                                            </div>
                                        ) : friends.length === 0 ? (
                                            <div className="col-span-full h-full flex flex-col md:flex-row items-center justify-center gap-8 relative min-h-0 overflow-hidden">
                                                {/* Speech Bubble (Left on desktop) */}
                                                <motion.div
                                                    initial={{ opacity: 0, x: -20, scale: 0.8 }}
                                                    animate={{ opacity: 1, x: 0, scale: 1 }}
                                                    transition={{ delay: 0.5, type: "spring", stiffness: 200, damping: 10 }}
                                                    className="relative bg-indigo-950/80 backdrop-blur-md text-white px-8 py-6 rounded-[2.5rem] rounded-br-none shadow-[0_10px_40px_rgba(0,0,0,0.5)] border border-white/10 z-20 max-w-sm text-center"
                                                >
                                                    <div className="flex flex-col items-center gap-2">
                                                        <div className="text-xl font-bold tracking-tight whitespace-nowrap">당신.. 친구가 없는건..</div>
                                                        <div className="text-xl font-bold tracking-tight">아니지..?</div>
                                                    </div>

                                                    {/* Bubble Tail - Now pointing Right */}
                                                    <div className="absolute top-1/2 -right-2 -translate-y-1/2 w-4 h-4 bg-indigo-950 border-t border-r border-white/10 transform rotate-45" />
                                                </motion.div>

                                                {/* Character Image (Right on desktop) */}
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.9, x: 20 }}
                                                    animate={{ opacity: 1, scale: 1, x: 0 }}
                                                    transition={{ duration: 0.5 }}
                                                    className="relative z-10 h-40 md:h-56 shrink-0 flex items-center justify-center"
                                                >
                                                    <img
                                                        src={getSDCharacterImage('east', charSettings.east, 'loading')}
                                                        alt="No Friends"
                                                        className="h-full w-auto object-contain drop-shadow-[0_20px_50px_rgba(99,102,241,0.3)] opacity-80"
                                                    />
                                                </motion.div>
                                            </div>
                                        ) : (
                                            friends
                                                .filter(f => f.nickname.includes(searchQuery))
                                                .map((friend) => (
                                                    <motion.div
                                                        key={friend.userId}
                                                        whileHover={{ y: -5 }}
                                                        className="group bg-white/5 border border-white/10 hover:border-indigo-500/40 rounded-3xl p-8 transition-all flex flex-col items-center shadow-lg relative overflow-hidden"
                                                    >
                                                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 blur-[40px] rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />

                                                        <div className="relative z-20 flex flex-col items-center w-full">
                                                            {/* Avatar - Modern Frame */}
                                                            <div className="relative mb-6">
                                                                <div className="absolute -inset-4 rounded-full border border-indigo-500/10 border-dashed animate-[spin_30s_linear_infinite] group-hover:border-indigo-500/30 transition-colors" />
                                                                <div className="relative w-28 h-28 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 shadow-2xl flex items-center justify-center text-4xl font-bold border-4 border-white/5 text-white">
                                                                    {friend.nickname[0]}
                                                                </div>
                                                                {/* Status Indicator */}
                                                                <div className="absolute bottom-2 right-2 w-6 h-6 bg-emerald-500 border-4 border-[#16161a] rounded-full shadow-lg" />
                                                            </div>

                                                            <div className="text-center w-full">
                                                                <h3 className="text-2xl font-bold text-white group-hover:text-indigo-300 transition-colors mb-6 truncate px-2">{friend.nickname}</h3>

                                                                <button
                                                                    onClick={() => handleDeleteFriend(friend.userId)}
                                                                    disabled={actionLoading === `delete-${friend.userId}`}
                                                                    className="w-full py-3 bg-red-500/5 hover:bg-red-500/10 text-red-400 border border-red-500/20 hover:border-red-500/40 text-xs font-bold rounded-xl transition-all active:scale-95 opacity-0 group-hover:opacity-100 uppercase tracking-widest"
                                                                >
                                                                    친구 삭제
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                ))
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
};

export default FriendsPage;
