import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, ArrowLeft, X } from 'lucide-react';
import CompatibilityResultView from '../results/CompatibilityResultView';
import HopaeNameplate from '../common/HopaeNameplate';
import { getMyFriends, type Friend } from '../../api/friend';
import { getUserInfo, type UserResponse } from '../../api/auth';
import { createCompatibility, type CompatibilityResponse } from '../../api/compatibility';
import { jwtDecode } from 'jwt-decode';
import { useSound } from '../../hooks/useSound';
import Modal from '../common/Modal';
import CustomSelect from '../common/CustomSelect';
import { useCharacterSettings, getCharacterName, getSDCharacterImage } from '../../utils/character';

type Phase = 'selection' | 'form' | 'loading' | 'comparison' | 'result';

interface CompatibilityPageProps {
    onMenuVisibilityChange?: (visible: boolean) => void;
}

const CompatibilityPage = ({ onMenuVisibilityChange }: CompatibilityPageProps) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { play, stop } = useSound();

    const [phase, setPhase] = useState<Phase>('form');
    const [loading, setLoading] = useState(true);
    const [friends, setFriends] = useState<Friend[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
    const [selectedType, setSelectedType] = useState<'west' | 'east' | null>(null);

    const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);

    const charSettings = useCharacterSettings();

    // Dynamic characters based on equipped status
    const equippedWest = getCharacterName('west', charSettings.west);
    const equippedEast = getCharacterName('east', charSettings.east);

    const [currentPastLifeChar, setCurrentPastLifeChar] = useState(0);
    const [showScrollLeft, setShowScrollLeft] = useState(false);
    const [showScrollRight, setShowScrollRight] = useState(false);
    const [isWestHovered, setIsWestHovered] = useState(false);
    const [isEastHovered, setIsEastHovered] = useState(false);

    // Modal State
    const [modal, setModal] = useState({
        isOpen: false,
        title: '',
        message: ''
    });

    // Compatibility Data State
    const [compatibilityResult, setCompatibilityResult] = useState<CompatibilityResponse | null>(null);

    // Friend Info Form State
    const [friendInfo, setFriendInfo] = useState({
        targetUserId: undefined as number | undefined,
        name: '',
        nickname: '' as string | undefined, // Added for fallback display logic
        gender: 'M' as 'M' | 'F',
        birthYear: '',
        birthMonth: '',
        birthDay: '',
        birthTime: '', // 24-hour format HH:mm
        isSolar: true
    });

    const resolveDisplayName = (nameKor: string | null | undefined, nickname: string | undefined): { name: string, subName?: string } => {
        if (nameKor && nameKor.trim()) {
            return { name: nameKor };
        }
        return {
            name: nickname || '?',
            subName: nickname
        };
    };

    const pastLifeChars = [
        '거상.png', '공주.png', '대장군.png', '여장군.png',
        '왕.png', '주모.png', '포도대장.png', '한량선비.png'
    ];

    const loadingMessages = [
        "전생에 두 분이 어떤 사이였는지 실타래를 풀고 있습니다.",
        "두 분의 애정 지수가 너무 높아 서버가 뜨거워지고 있습니다!",
        "비정상적으로 높은 궁합 수치 감지! 데이터 무결성 확인 중...",
        "운명의 데스티니 모듈을 로드하는 중...",
        "두 분의 사주 팔자 52만 가지 경우의 수를 대조하고 있어요...",
    ];

    const scrollRef = useRef<HTMLDivElement>(null);
    const mainScrollRef = useRef<HTMLDivElement>(null);

    // Update scroll indicator visibility
    const updateScrollButtons = () => {
        if (scrollRef.current) {
            const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
            setShowScrollLeft(scrollLeft > 10);
            setShowScrollRight(scrollLeft + clientWidth < scrollWidth - 10);
        }
    };

    const handleManualScroll = (direction: 'left' | 'right') => {
        if (scrollRef.current) {
            const scrollAmount = 400;
            scrollRef.current.scrollBy({
                left: direction === 'left' ? -scrollAmount : scrollAmount,
                behavior: 'smooth'
            });
            play('SFX', 'SEAL_CLICK');
        }
    };

    useEffect(() => {
        updateScrollButtons();
        const timer = setTimeout(updateScrollButtons, 500);
        return () => clearTimeout(timer);
    }, [phase, loading, friends]);

    useEffect(() => {
        if (phase !== 'selection' || loading) return;

        const handleWheel = (e: WheelEvent) => {
            if (e.deltaY === 0) return;
            const el = scrollRef.current;
            if (!el) return;

            e.preventDefault();
            el.scrollLeft += e.deltaY * 2;
        };

        window.addEventListener('wheel', handleWheel, { passive: false });
        return () => window.removeEventListener('wheel', handleWheel);
    }, [phase, loading]);

    useEffect(() => {
        onMenuVisibilityChange?.(false);
        return () => {
            onMenuVisibilityChange?.(true);
        };
    }, [onMenuVisibilityChange]);

    useEffect(() => {
        if (selectedType && mainScrollRef.current) {
            mainScrollRef.current.scrollTo({ top: 0, behavior: 'instant' });
        }
    }, [selectedType]);

    useEffect(() => {
        play('BGM', 'EAST3', { loop: true, volume: 0.4 });
        return () => {
            stop('BGM', 'EAST3');
        };
    }, [play, stop]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('accessToken');
            if (token) {
                const decoded: any = jwtDecode(token);
                const userData = await getUserInfo(decoded.userId);
                setCurrentUser(userData);
            }
            const friendData = await getMyFriends();
            setFriends(friendData);

            const stateFriend = (location.state as any)?.selectedFriend as Friend;
            if (stateFriend) {
                await selectFriendAction(stateFriend);
            }
        } catch (err) {
            console.error('Failed to load initial data:', err);
            setFriends([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleFriendSelect = async (friend: Friend) => {
        play('SFX', 'SEAL_CLICK');
        await selectFriendAction(friend);
    };

    const selectFriendAction = async (friend: Friend) => {
        try {
            const friendData = await getUserInfo(friend.userId);
            let y = '', m = '', d = '';
            if (friendData.birthDate) {
                const parts = friendData.birthDate.split('-');
                if (parts.length === 3) {
                    y = parts[0];
                    m = parts[1];
                    d = parts[2];
                }
            }

            let bTime = '';
            if (friendData.birthTime) {
                // Assuming format HH:mm:ss or HH:mm
                const parts = friendData.birthTime.split(':');
                if (parts.length >= 2) {
                    bTime = `${parts[0]}:${parts[1]}`;
                }
            }

            setFriendInfo({
                targetUserId: friend.userId,
                name: friendData.nameKor || '',
                nickname: friendData.nickname,
                gender: friendData.gender === 'F' ? 'F' : 'M',
                birthYear: y || '',
                birthMonth: m || '',
                birthDay: d || '',
                birthTime: bTime,
                isSolar: friendData.isSolar ?? true
            });
        } catch (err) {
            console.error('Failed to fetch friend detail:', err);
            setFriendInfo(prev => ({
                ...prev,
                targetUserId: friend.userId,
                name: friend.nickname || '',
                nickname: friend.nickname,
            }));
        }
        setPhase('form');
    };

    const handleStartAnalysis = async () => {
        if (!friendInfo.name.trim()) {
            setModal({ isOpen: true, title: '안내', message: '이름을 입력해주세요.' });
            return;
        }
        if (!friendInfo.birthYear || !friendInfo.birthMonth || !friendInfo.birthDay) {
            setModal({ isOpen: true, title: '안내', message: '생년월일을 모두 입력해주세요.' });
            return;
        }
        // Removed birthTime validation as per instruction snippet

        play('SFX', 'SEAL_CLICK');
        setPhase('loading');
        setLoadingMessageIndex(0);

        try {
            const birthDate = `${friendInfo.birthYear}-${friendInfo.birthMonth.toString().padStart(2, '0')}-${friendInfo.birthDay.toString().padStart(2, '0')}`;

            // Construct Payload
            const payload: any = {
                targetName: friendInfo.name,
                relationType: 'LOVE',
                birthData: {
                    gender: friendInfo.gender,
                    is_solar: friendInfo.isSolar,
                    birth_date: birthDate,
                    birth_time: friendInfo.birthTime || undefined
                }
            };

            if (friendInfo.targetUserId) {
                payload.targetUserId = friendInfo.targetUserId;
            }


            // Call createCompatibility with minimum loading time (7-9 seconds)
            const minDelay = Math.floor(Math.random() * 2000) + 7000;
            const minDelayPromise = new Promise(resolve => setTimeout(resolve, minDelay));

            const [result] = await Promise.all([
                createCompatibility(payload),
                minDelayPromise
            ]);

            setCompatibilityResult(result);
            setPhase('comparison');

        } catch (error) {
            console.error("Compatibility Analysis Failed:", error);
            setModal({ isOpen: true, title: '오류', message: '분석 중 오류가 발생했습니다. 다시 시도해주세요.' });
            setPhase('form');
        }
    };

    useEffect(() => {
        let interval: any;
        if (phase === 'loading') {
            interval = setInterval(() => {
                setLoadingMessageIndex(prev => {
                    let next;
                    do { next = Math.floor(Math.random() * loadingMessages.length); } while (next === prev && loadingMessages.length > 1);
                    return next;
                });
                setCurrentPastLifeChar(prev => {
                    let next;
                    do { next = Math.floor(Math.random() * pastLifeChars.length); } while (next === prev && pastLifeChars.length > 1);
                    return next;
                });
            }, 3300);
        }
        return () => clearInterval(interval);
    }, [phase, loadingMessages.length, pastLifeChars.length]);

    const handleManualEntry = () => {
        play('SFX', 'SEAL_CLICK');
        setFriendInfo({
            targetUserId: undefined,
            name: '',
            nickname: undefined,
            gender: 'M', birthYear: '', birthMonth: '', birthDay: '',
            birthTime: '', isSolar: true
        });
        setPhase('form');
    };

    const handleBack = () => {
        if (phase === 'form') navigate('/home');
        else if (phase === 'selection') setPhase('form');
        else {
            setPhase('form');
            setSearchTerm('');
        }
    };

    const filteredFriends = friends.filter(friend => {
        if (!searchTerm.trim()) return true;
        const searchLower = searchTerm.toLowerCase();
        return (friend.name?.toLowerCase().includes(searchLower) || friend.nickname.toLowerCase().includes(searchLower));
    });

    return (
        <div className="fixed inset-0 z-50 bg-[#0c0a09] text-white overflow-hidden font-['Hahmlet']">
            <div className="absolute inset-0 pointer-events-none">
                {/* Base background image - Updated to todayfortune.png */}
                <div
                    className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-60 transition-opacity duration-1000"
                    style={{ backgroundImage: "url('/assets/bg/todayfortune.png')" }}
                />

                {/* Top gradient blend to handle vertically long screens */}
                <div className="absolute inset-0 bg-gradient-to-b from-[#0c0a09] via-[#0c0a09]/20 to-transparent h-[40%]" />

                {/* Global darkening overlay */}
                <div className="absolute inset-0 bg-black/60" />
            </div>

            {/* Top Navigation - Hwatu Style */}
            <div className="absolute top-0 left-0 w-full p-8 flex justify-between items-center z-[110] pointer-events-none h-32">
                <motion.button
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleBack}
                    className={`pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full backdrop-blur-xl border transition-all shadow-lg font-['Hahmlet']
                        ${(phase === 'result' && selectedType === 'west')
                            ? 'bg-purple-950/60 border-purple-400/40 text-purple-100 hover:bg-purple-900/80 shadow-purple-500/10'
                            : 'bg-stone-900/60 border-amber-900/40 text-amber-100 hover:bg-stone-800/80 shadow-amber-900/10'
                        }`}
                >
                    <ArrowLeft size={18} />
                    <span className="text-sm font-medium tracking-wider">뒤로가기</span>
                </motion.button>

                <motion.button
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => { play('SFX', 'SEAL_CLICK'); navigate('/home'); }}
                    className={`pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full backdrop-blur-xl border transition-all shadow-lg font-['Hahmlet']
                        ${(phase === 'result' && selectedType === 'west')
                            ? 'bg-purple-950/60 border-purple-400/40 text-purple-100 hover:bg-purple-900/80 shadow-purple-500/10'
                            : 'bg-stone-900/60 border-amber-900/40 text-amber-100 hover:bg-stone-800/80 shadow-amber-900/10'
                        }`}
                >
                    <span className="text-sm font-medium tracking-wider">나가기</span>
                    <X size={18} />
                </motion.button>
            </div>

            <div ref={mainScrollRef} className="relative z-10 w-full h-full flex flex-col items-center pt-0 pb-0 overflow-y-auto scrollbar-hide">
                <AnimatePresence mode="wait">
                    {phase === 'selection' && (
                        <motion.div key="selection" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="w-full h-full flex flex-col items-center justify-start max-w-7xl mx-auto px-4">
                            <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }} className="mt-12 mb-1 text-center flex-shrink-0">
                                <h1 className="text-4xl md:text-5xl font-['Hahmlet'] font-light text-white/90 mb-2 tracking-tight">궁합을 확인할 상대를 <span className="text-amber-500">선택</span>하세요</h1>
                                <div className="flex flex-col md:flex-row items-center justify-center gap-4 mt-4">
                                    <div className="relative w-full max-w-md group bg-[#f0e6d2]/5 border border-amber-900/30 rounded-lg backdrop-blur-md px-4 py-2">
                                        <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="친구의 이름/닉네임을 입력하세요" className="bg-transparent border-none outline-none w-full px-3 text-amber-100 placeholder:text-white/40 tracking-widest text-sm" />
                                    </div>
                                </div>
                                <div className="flex justify-center mt-6 relative z-50">
                                    <button onClick={handleManualEntry} className="px-8 py-3 bg-amber-900/30 text-amber-200/80 rounded-full border border-amber-800/20 hover:bg-amber-800/40 transition-all text-sm tracking-[0.2em] flex items-center gap-2 group pointer-events-auto">
                                        <span>직접 입력하여 궁합보기</span>
                                        <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
                                    </button>
                                </div>
                            </motion.div>

                            {loading ? (
                                <div className="flex-1 flex flex-col items-center justify-center gap-4">
                                    <div className="w-12 h-12 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
                                </div>
                            ) : friends.length === 0 ? (
                                <div className="flex-1 flex flex-col items-center justify-center">
                                    <button onClick={() => navigate('/friends')} className="px-6 py-2 bg-amber-900/40 text-amber-200/80 rounded border border-amber-700/30">친구 맺으러 가기</button>
                                </div>
                            ) : (
                                <div className="relative w-full group/scroll flex flex-col justify-center min-h-[550px] overflow-visible">
                                    <AnimatePresence>
                                        {showScrollLeft && (
                                            <motion.button initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} onClick={() => handleManualScroll('left')} className="absolute left-10 top-1/2 -translate-y-1/2 z-40 p-4 rounded-full bg-amber-900/20 border border-amber-500/30 text-amber-500/60 transition-all backdrop-blur-sm">
                                                <ChevronLeft size={48} />
                                            </motion.button>
                                        )}
                                    </AnimatePresence>
                                    <AnimatePresence>
                                        {showScrollRight && (
                                            <motion.button initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} onClick={() => handleManualScroll('right')} className="absolute right-10 top-1/2 -translate-y-1/2 z-40 p-4 rounded-full bg-amber-900/20 border border-amber-500/30 text-amber-500/60 transition-all backdrop-blur-sm">
                                                <ChevronRight size={48} />
                                            </motion.button>
                                        )}
                                    </AnimatePresence>
                                    <div ref={scrollRef} onScroll={updateScrollButtons} className="scrollbar-hide relative z-10 w-full overflow-x-auto snap-x flex items-center gap-12 justify-start px-[10%] min-h-[500px] overflow-y-visible">
                                        {filteredFriends.map((friend, idx) => (
                                            <motion.div key={friend.userId} initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }} onClick={() => handleFriendSelect(friend)} className="relative flex-shrink-0 cursor-pointer snap-center">
                                                <HopaeNameplate name={friend.nickname} />
                                            </motion.div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {phase === 'form' && (
                        <motion.div key="form" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="flex-1 w-full max-w-2xl mx-auto flex flex-col items-center justify-center relative px-6 py-4 md:py-8">
                            <div className="relative w-full bg-[#fdfaf3] rounded-sm shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-l-8 border-amber-900/60 p-6 md:p-10 overflow-hidden text-amber-950">
                                <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/handmade-paper.png')" }} />
                                <h2 className="relative z-10 text-2xl md:text-3xl font-bold mb-6 tracking-widest text-center">상대방 <span className="text-amber-700">사주 정보</span> 입력</h2>
                                <div className="relative z-10 space-y-4 max-w-md mx-auto">
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs text-amber-900/60 font-medium tracking-[0.2em] px-1">이름</label>
                                        <input
                                            type="text"
                                            maxLength={6}
                                            value={friendInfo.name}
                                            onChange={(e) => {
                                                setFriendInfo({ ...friendInfo, name: e.target.value.slice(0, 6) });
                                            }}
                                            className="w-full bg-amber-500/5 border-b-2 border-amber-900/20 focus:border-amber-700 outline-none px-4 py-3 text-amber-950 transition-all font-['Hahmlet']"
                                            placeholder="이름"
                                        />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs text-amber-900/60 font-medium tracking-[0.2em] px-1">성별</label>
                                        <div className="flex gap-4">
                                            {['M', 'F'].map((g) => (
                                                <button key={g} onClick={() => setFriendInfo({ ...friendInfo, gender: g as 'M' | 'F' })} className={`flex-1 py-3 rounded-md border transition-all ${friendInfo.gender === g ? 'bg-amber-900 text-amber-50' : 'bg-transparent text-amber-900/40 border-amber-900/10'}`}>{g === 'M' ? '남성' : '여성'}</button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <div className="flex justify-between items-end px-1">
                                            <label className="text-xs text-amber-900/60 font-medium tracking-[0.2em]">생년월일</label>
                                            <div className="flex bg-amber-500/10 p-0.5 rounded-md border border-amber-900/10 mb-1">
                                                {[true, false].map((solar) => (
                                                    <button key={solar ? 'solar' : 'lunar'} onClick={() => setFriendInfo({ ...friendInfo, isSolar: solar })} className={`px-3 py-1 rounded text-[10px] font-bold ${friendInfo.isSolar === solar ? 'bg-amber-900 text-white' : 'text-amber-900/40'}`}>{solar ? '양력' : '음력'}</button>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <input type="text" maxLength={4} value={friendInfo.birthYear} onChange={(e) => setFriendInfo({ ...friendInfo, birthYear: e.target.value.replace(/[^0-9]/g, '') })} className="flex-1 bg-amber-500/5 border-b-2 border-amber-900/20 px-3 py-3 text-center" placeholder="연도" />
                                            {/* 월 선택 */}
                                            <div className="w-24">
                                                <CustomSelect
                                                    value={friendInfo.birthMonth}
                                                    options={[
                                                        { value: '', label: '월' },
                                                        ...Array.from({ length: 12 }, (_, i) => ({
                                                            value: (i + 1).toString().padStart(2, '0'),
                                                            label: `${i + 1}월`
                                                        }))
                                                    ]}
                                                    onChange={(m: string) => setFriendInfo({ ...friendInfo, birthMonth: m })}
                                                    placeholder="월"
                                                />
                                            </div>
                                            {/* 일 선택 */}
                                            <div className="w-24">
                                                <CustomSelect
                                                    value={friendInfo.birthDay}
                                                    options={[
                                                        { value: '', label: '일' },
                                                        ...Array.from({ length: 31 }, (_, i) => ({
                                                            value: (i + 1).toString().padStart(2, '0'),
                                                            label: `${i + 1}일`
                                                        }))
                                                    ]}
                                                    onChange={(d: string) => setFriendInfo({ ...friendInfo, birthDay: d })}
                                                    placeholder="일"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs text-amber-900/60 font-medium tracking-[0.2em] px-1">태어난 시간</label>
                                        <div className="flex items-center gap-2">
                                            {/* 시 선택 */}
                                            <CustomSelect
                                                value={friendInfo.birthTime ? friendInfo.birthTime.split(':')[0] : ''}
                                                options={[
                                                    { value: '', label: '시 (모름)' },
                                                    ...Array.from({ length: 24 }, (_, i) => ({
                                                        value: i.toString().padStart(2, '0'),
                                                        label: `${i.toString().padStart(2, '0')}시`
                                                    }))
                                                ]}
                                                onChange={(h: string) => {
                                                    if (!h) setFriendInfo({ ...friendInfo, birthTime: '' });
                                                    else setFriendInfo({ ...friendInfo, birthTime: `${h}:00` });
                                                }}
                                                placeholder="시 (모름)"
                                            />
                                        </div>
                                        <p className="text-[10px] text-amber-900/40 text-center tracking-tight mt-1">* 태어난 시각을 모른다면 그대로 두고 진행해주세요.</p>
                                    </div>
                                    <div className="flex flex-col gap-3 mt-8">
                                        <motion.button onClick={handleStartAnalysis} whileHover={{ scale: 1.01 }} className="w-full py-4 bg-amber-900 text-amber-50 font-bold tracking-[0.4em] shadow-xl rounded-sm">궁합 분석 시작</motion.button>
                                        <button onClick={() => setPhase('selection')} className="w-full py-2 text-amber-900/40 text-sm tracking-widest">친구 목록 보기</button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {phase === 'loading' && (
                        <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 w-full max-w-4xl mx-auto flex flex-col items-center justify-center relative -mt-28">
                            <AnimatePresence mode="wait">
                                <motion.h2 key={loadingMessageIndex} initial={{ y: 5, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -5, opacity: 0 }} className="text-2xl font-medium text-amber-100/90 mt-6 mb-24 tracking-[0.3em] text-center">{loadingMessages[loadingMessageIndex]}</motion.h2>
                            </AnimatePresence>
                            <div className="relative flex justify-between items-center w-full px-20 h-64 z-10 mt-8">
                                <motion.div initial={{ x: -100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="relative z-20">
                                    <HopaeNameplate {...resolveDisplayName(currentUser?.nameKor, currentUser?.nickname)} />
                                </motion.div>
                                <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-30 flex flex-col items-center">
                                    <AnimatePresence mode="wait">
                                        <motion.div key={currentPastLifeChar} initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1.25 }} exit={{ opacity: 0, scale: 0.5 }} className="w-56 h-56 md:w-72 md:h-72"><img src={`/assets/character/east/전생/${pastLifeChars[currentPastLifeChar]}`} className="w-full h-full object-contain drop-shadow-[0_0_35px_rgba(251,191,36,0.7)]" /></motion.div>
                                    </AnimatePresence>
                                </div>
                                <motion.div initial={{ x: 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="relative z-20">
                                    <HopaeNameplate {...resolveDisplayName(friendInfo.name, friendInfo.nickname)} />
                                </motion.div>
                            </div>
                        </motion.div>
                    )}

                    {phase === 'comparison' && (
                        <motion.div key="comparison" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 w-full max-w-6xl mx-auto flex flex-col items-center justify-center relative px-6">
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.5 }}
                                className="bg-stone-900/40 backdrop-blur-xl border border-amber-400/20 px-10 md:px-16 py-4 md:py-6 rounded-full shadow-2xl shadow-amber-900/20 translate-y-24 mb-16 flex-none"
                            >
                                <h2 className="text-2xl md:text-5xl font-extrabold tracking-[0.2em] bg-gradient-to-r from-gray-300 via-gray-100 to-gray-300 bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(255,255,255,0.1)] text-center">
                                    먼저 보고싶은 분석을 골라주세요
                                </h2>
                            </motion.div>
                            <div className="flex-1 min-h-0 w-full flex flex-col items-center justify-center">
                                <div className="flex flex-col md:flex-row items-stretch justify-center gap-6 md:gap-8 w-full max-w-5xl px-4 h-full max-h-[min(600px,55vh)]">
                                    <motion.div
                                        onMouseEnter={() => setIsWestHovered(true)}
                                        onMouseLeave={() => setIsWestHovered(false)}
                                        whileHover={{ scale: 1.02, y: -5 }}
                                        className="group relative flex flex-col items-center cursor-pointer bg-stone-900/40 backdrop-blur-xl border border-purple-400/30 hover:border-purple-400/50 rounded-[2.5rem] p-6 md:p-8 transition-all duration-500 shadow-2xl hover:shadow-purple-500/10 overflow-hidden flex-1"
                                        onClick={() => { play('SFX', 'BUTTON_SELECT'); setSelectedType('west'); setPhase('result'); }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                                        {/* Unified Speech Bubble for Stella */}
                                        <motion.div
                                            animate={{ y: [0, -5, 0] }}
                                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                                            className="absolute top-6 left-1/2 -translate-x-1/2 z-20 bg-stone-900/80 backdrop-blur-md border border-amber-400/20 px-4 py-2 rounded-xl shadow-xl text-amber-100 text-xs md:text-sm font-medium whitespace-nowrap"
                                        >
                                            별들의 선택을 믿어봐!
                                        </motion.div>

                                        <div className="relative flex-1 w-full flex items-center justify-center min-h-0">
                                            <motion.img
                                                src={getSDCharacterImage('west', charSettings.west, isWestHovered ? 'smile' : 'normal')}
                                                className="h-full w-auto max-w-full object-contain"
                                                animate={{ y: [0, -10, 0] }}
                                                transition={{ duration: 4, repeat: Infinity }}
                                            />
                                        </div>
                                        <h3 className="relative z-10 text-base md:text-xl font-bold text-purple-200 mt-4 tracking-widest text-center flex-none">{equippedWest}의 별자리 궁합</h3>
                                    </motion.div>

                                    <motion.div
                                        onMouseEnter={() => setIsEastHovered(true)}
                                        onMouseLeave={() => setIsEastHovered(false)}
                                        whileHover={{ scale: 1.02, y: -5 }}
                                        className="group relative flex flex-col items-center cursor-pointer bg-stone-900/40 backdrop-blur-xl border border-amber-400/10 hover:border-amber-400/40 rounded-[2.5rem] p-6 md:p-8 transition-all duration-500 shadow-2xl hover:shadow-amber-500/10 overflow-hidden flex-1"
                                        onClick={() => { play('SFX', 'SEAL_CLICK'); setSelectedType('east'); setPhase('result'); }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                                        {/* Unified Speech Bubble for Soiseol */}
                                        <motion.div
                                            animate={{ y: [0, -5, 0] }}
                                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                                            className="absolute top-6 left-1/2 -translate-x-1/2 z-20 bg-stone-900/80 backdrop-blur-md border border-amber-400/20 px-4 py-2 rounded-xl shadow-xl text-amber-100 text-xs md:text-sm font-medium whitespace-nowrap"
                                        >
                                            운명의 깊이를 느껴보게.
                                        </motion.div>

                                        <div className="relative flex-1 w-full flex items-center justify-center min-h-0">
                                            <motion.img
                                                src={getSDCharacterImage('east', charSettings.east, isEastHovered ? 'smile' : 'normal')}
                                                className="h-full w-auto max-w-full object-contain"
                                                animate={{ y: [0, -10, 0] }}
                                                transition={{ duration: 4, repeat: Infinity, delay: 0.5 }}
                                            />
                                        </div>
                                        <h3 className="relative z-10 text-base md:text-xl font-bold text-amber-200 mt-4 tracking-widest text-center flex-none">{equippedEast}의 사주 궁합</h3>
                                    </motion.div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {phase === 'result' && (
                        <motion.div
                            key="result"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="w-full h-full"
                        >
                            <CompatibilityResultView
                                data={compatibilityResult}
                                initialType={selectedType || 'east'}
                                userInfo={{ name: resolveDisplayName(currentUser?.nameKor, currentUser?.nickname).name }}
                                friendInfo={{ name: resolveDisplayName(friendInfo.name, friendInfo.nickname).name }}
                                onBack={() => setPhase('comparison')}
                                onExit={() => navigate('/')}
                                onTypeChange={setSelectedType}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <Modal
                isOpen={modal.isOpen}
                onClose={() => setModal({ ...modal, isOpen: false })}
                title={modal.title}
                message={modal.message}
                type="info"
                confirmText="확인"
            />
        </div>
    );
};



export default CompatibilityPage;
