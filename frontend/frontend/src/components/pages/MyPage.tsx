import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    User, Camera, Edit2, Save, X, LogOut, Lock,
    Trash2, Mail, Hammer, Settings, Sparkles, RefreshCcw, Orbit
} from 'lucide-react';
import { getWesternZodiac, calculateFiveElements } from '../../utils/sajuUtils';
import { useNavigate } from 'react-router-dom';
import { getUserInfo, updateProfile, type UserResponse } from '../../api/auth';
import { jwtDecode } from 'jwt-decode';
import Modal from '../common/Modal';
import PasswordChangeModal from '../common/PasswordChangeModal';
import AccountDeleteModal from '../common/AccountDeleteModal';
import SettingsModal from '../common/SettingsModal';

const MyPage = () => {
    const navigate = useNavigate();
    const [isEditing, setIsEditing] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showPasswordChangeModal, setShowPasswordChangeModal] = useState(false);
    const [showSettingsModal, setShowSettingsModal] = useState(false);
    const [showLogoutModal, setShowLogoutModal] = useState(false);

    // Modal State
    const [modalConfig, setModalConfig] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        type: 'info' | 'error' | 'success';
        redirect?: string;
    }>({
        isOpen: false,
        title: '',
        message: '',
        type: 'info'
    });

    // User Data State
    const [user, setUser] = useState<UserResponse | null>(null);
    const [loading, setLoading] = useState(true);

    const closeModal = () => {
        setModalConfig(prev => ({ ...prev, isOpen: false }));
        if (modalConfig.redirect) {
            navigate(modalConfig.redirect);
        }
    };

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                const token = localStorage.getItem('accessToken');
                if (!token) {
                    setLoading(false);
                    setModalConfig({
                        isOpen: true,
                        title: '로그인 필요',
                        message: '로그인이 필요한 서비스입니다.',
                        type: 'error',
                        redirect: '/'
                    });
                    return;
                }

                // Decode Token to get userId
                const decoded: any = jwtDecode(token);
                const userId = decoded.userId;

                if (!userId) {
                    throw new Error('토큰에 회원 정보가 없습니다.');
                }

                // Fetch User Info
                const data = await getUserInfo(userId);
                setUser(data);
            } catch (error) {
                console.error('Failed to fetch user info:', error);
                setModalConfig({
                    isOpen: true,
                    title: '오류',
                    message: '회원 정보를 불러오는데 실패했습니다.',
                    type: 'error',
                    redirect: '/'
                });
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, [navigate]);

    // Mock Edit Form (Synced with real data)
    const [editForm, setEditForm] = useState({
        nickname: '',
        nameKor: '',
        birthDate: '',
        birthTime: '',
        isSolar: true,
        gender: '' as 'M' | 'F' | ''
    });

    useEffect(() => {
        if (user) {
            setEditForm({
                nickname: user.nickname || '',
                nameKor: user.nameKor || '',
                birthDate: user.birthDate || '',
                birthTime: user.birthTime || '',
                isSolar: user.isSolar ?? true,
                gender: user.gender || ''
            });
        }
    }, [user]);

    const handleSave = async () => {
        // Validation
        if (!editForm.nameKor.trim()) {
            setModalConfig({ isOpen: true, title: '입력 오류', message: '이름을 입력해주세요.', type: 'error' });
            return;
        }
        if (!editForm.nickname.trim()) {
            setModalConfig({ isOpen: true, title: '입력 오류', message: '닉네임을 입력해주세요.', type: 'error' });
            return;
        }

        try {
            const updatedUser = await updateProfile({
                nickname: editForm.nickname,
                nameKor: editForm.nameKor,
                birthDate: editForm.birthDate || undefined,
                birthTime: editForm.birthTime || undefined,
                isSolar: editForm.isSolar,
                gender: editForm.gender || undefined
            });

            setUser(updatedUser); // Update local user state
            setIsEditing(false);
            setModalConfig({
                isOpen: true,
                title: '성공',
                message: '회원 정보가 수정되었습니다.',
                type: 'success'
            });
        } catch (error: any) {
            console.error('Update Failed:', error);
            const errorMessage = error.response?.data?.message || '정보 수정에 실패했습니다.';
            setModalConfig({
                isOpen: true,
                title: '오류',
                message: errorMessage,
                type: 'error'
            });
        }
    };

    const handleDeleteSuccess = () => {
        localStorage.clear();
        setModalConfig({
            isOpen: true,
            title: '탈퇴 완료',
            message: '회원 탈퇴가 처리되었습니다. 이용해 주셔서 감사합니다.',
            type: 'success',
            redirect: '/'
        });
    };

    const handleLogout = () => {
        setShowLogoutModal(true);
    };

    const handleLogoutConfirm = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        navigate('/');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0b0d14] flex flex-col items-center justify-center text-white">
                <div className="w-16 h-16 border-4 border-t-indigo-500 border-white/10 rounded-full animate-spin mb-4" />
                <p className="font-['GmarketSansMedium'] text-lg animate-pulse">운명을 읽어오는 중...</p>
            </div>
        );
    }

    const fiveElements = user ? calculateFiveElements(user.birthDate, user.birthTime) : [];
    const zodiac = user ? getWesternZodiac(user.birthDate) : { name: '알 수 없음', icon: '✨' };

    const ProfileRadarChart = ({ data }: { data: any[] }) => {
        const size = 180;
        const center = size / 2;
        const radius = 60;

        // Find max value(s)
        const maxValue = Math.max(...data.map(d => d.value));
        const topElements = data.filter(d => d.value === maxValue);
        const topColors = topElements.map(e => e.color);

        const getPoint = (index: number, value: number) => {
            const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
            const dist = (value / 50) * radius; // Max scale 50%
            return {
                x: center + Math.cos(angle) * dist,
                y: center + Math.sin(angle) * dist
            };
        };

        const dataPoints = data.map((d, i) => getPoint(i, d.value));
        const dataPath = dataPoints.map(p => `${p.x},${p.y}`).join(' ');

        // Sparkle generator for stars
        const stars = Array.from({ length: 8 }).map((_, i) => ({
            id: i,
            x: Math.random() * size,
            y: Math.random() * size,
            delay: Math.random() * 2,
            duration: 1.5 + Math.random()
        }));

        return (
            <div className="relative flex flex-col items-center">
                <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
                    <defs>
                        <motion.radialGradient
                            id="radarGrad"
                            cx="50%" cy="50%" r="50%"
                            animate={{
                                stopColor: topColors.length > 1 ? topColors : undefined
                            }}
                            transition={topColors.length > 1 ? {
                                duration: 3,
                                repeat: Infinity,
                                ease: "easeInOut"
                            } : undefined}
                        >
                            <stop offset="0%" stopColor="inherit" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="inherit" stopOpacity="0.1" />
                        </motion.radialGradient>
                    </defs>

                    {/* Background circles/grid */}
                    {[10, 20, 30, 40, 50].map(level => (
                        <polygon
                            key={level}
                            points={Array.from({ length: 5 }).map((_, i) => {
                                const p = getPoint(i, level);
                                return `${p.x},${p.y}`;
                            }).join(' ')}
                            className="fill-none stroke-white/10 stroke-[0.5]"
                        />
                    ))}

                    <motion.polygon
                        points={dataPath}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{
                            opacity: 1,
                            scale: 1,
                            stroke: topColors.length > 1 ? topColors : topColors[0]
                        }}
                        transition={{
                            opacity: { duration: 1 },
                            scale: { duration: 1 },
                            stroke: topColors.length > 1 ? { duration: 3, repeat: Infinity, ease: "easeInOut" } : undefined
                        }}
                        fill="url(#radarGrad)"
                        strokeWidth="2"
                        className="drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]"
                    />

                    {/* Sparkling Stars */}
                    {stars.map(star => (
                        <motion.circle
                            key={star.id}
                            cx={star.x}
                            cy={star.y}
                            r={0.8}
                            fill="white"
                            initial={{ opacity: 0 }}
                            animate={{
                                opacity: [0, 1, 0],
                                scale: [0, 1.2, 0],
                                filter: ["blur(0px)", "blur(1px)", "blur(0px)"]
                            }}
                            transition={{
                                duration: star.duration,
                                repeat: Infinity,
                                delay: star.delay,
                                ease: "easeInOut"
                            }}
                        />
                    ))}

                    {data.map((l, i) => {
                        const p = getPoint(i, 65);
                        return (
                            <text
                                key={l.name}
                                x={p.x}
                                y={p.y}
                                fill="white"
                                fontSize="12"
                                textAnchor="middle"
                                dominantBaseline="middle"
                                className="font-['GmarketSansMedium'] opacity-60"
                            >
                                {l.hanja}
                            </text>
                        );
                    })}
                </svg>
            </div>
        );
    };

    return (
        <>
            <Modal
                isOpen={modalConfig.isOpen}
                onClose={closeModal}
                title={modalConfig.title}
                message={modalConfig.message}
                type={modalConfig.type}
            />

            <Modal
                isOpen={showLogoutModal}
                onClose={() => setShowLogoutModal(false)}
                title="로그아웃"
                message="정말 로그아웃 하시겠습니까?"
                showCancel={true}
                onConfirm={handleLogoutConfirm}
            />

            {user && (
                <PasswordChangeModal
                    isOpen={showPasswordChangeModal}
                    onClose={() => setShowPasswordChangeModal(false)}
                    email={user.email}
                    onSuccess={() => {
                        setModalConfig({
                            isOpen: true,
                            title: '성공',
                            message: '비밀번호가 성공적으로 변경되었습니다.',
                            type: 'success'
                        });
                    }}
                />
            )}

            {user && (
                <SettingsModal
                    isOpen={showSettingsModal}
                    onClose={() => setShowSettingsModal(false)}
                    userId={user.id}
                />
            )}

            {user && (
                <AccountDeleteModal
                    isOpen={showDeleteModal}
                    onClose={() => setShowDeleteModal(false)}
                    email={user.email}
                    onSuccess={handleDeleteSuccess}
                />
            )}

            {user ? (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-full h-screen relative p-6 pt-24 bg-[#0b0d14] text-white overflow-y-auto font-['Pretendard'] custom-scrollbar"
                >
                    {/* Background Effects */}
                    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0b0d14] to-black pointer-events-none fixed" />

                    <div className="relative z-10 max-w-4xl mx-auto w-full space-y-6 pb-20">

                        {/* Header */}
                        <div className="flex items-center justify-between mb-8">
                            <h1 className="text-3xl font-bold font-gmarket flex items-center gap-2">
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">마이페이지</span>
                            </h1>
                            <div className="flex items-center gap-3">
                                {/* Dev Badge Removed */}
                                <button
                                    onClick={() => setShowSettingsModal(true)}
                                    className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                                    title="설정"
                                >
                                    <Settings size={20} className="text-indigo-400" />
                                </button>
                            </div>
                        </div>

                        {/* 1. Profile Section */}
                        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 md:p-10 flex flex-col md:flex-row items-start md:items-center gap-8 shadow-2xl">

                            {/* Avatar Area */}
                            <div className="relative group mx-auto md:mx-0">
                                <div className="w-32 h-32 md:w-40 md:h-40 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 p-1 shadow-lg ring-4 ring-white/5">
                                    {user.profileImg ? (
                                        <img src={user.profileImg} alt="Profile" className="w-full h-full rounded-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full rounded-full bg-[#1a1a2e] flex items-center justify-center overflow-hidden">
                                            <span className="text-5xl font-bold font-gmarket text-white/90">{user.nameKor ? user.nameKor[0] : user.nickname[0]}</span>
                                        </div>
                                    )}
                                </div>
                                <button className="absolute bottom-2 right-2 w-10 h-10 bg-white text-indigo-900 rounded-full flex items-center justify-center shadow-lg hover:bg-gray-200 transition-colors">
                                    <Camera size={20} />
                                </button>
                            </div>

                            {/* Info Area */}
                            <div className="flex-1 w-full text-center md:text-left">
                                {isEditing ? (
                                    <div className="space-y-4 max-w-md mx-auto md:mx-0">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {/* Name Input */}
                                            <div className="space-y-1 text-left">
                                                <label className="text-xs text-white/50 ml-1">이름</label>
                                                <input
                                                    type="text"
                                                    value={editForm.nameKor}
                                                    onChange={(e) => setEditForm({ ...editForm, nameKor: e.target.value })}
                                                    className="w-full h-10 px-4 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:bg-white/10 transition-all"
                                                    placeholder="이름 입력"
                                                />
                                            </div>

                                            {/* Nickname Input */}
                                            <div className="space-y-1 text-left">
                                                <label className="text-xs text-white/50 ml-1">닉네임</label>
                                                <input
                                                    type="text"
                                                    value={editForm.nickname}
                                                    onChange={(e) => setEditForm({ ...editForm, nickname: e.target.value })}
                                                    className="w-full h-10 px-4 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:bg-white/10 transition-all"
                                                    placeholder="닉네임 입력"
                                                />
                                            </div>

                                            {/* Birth Date */}
                                            <div className="space-y-1 text-left">
                                                <label className="text-xs text-white/50 ml-1">생년월일</label>
                                                <input
                                                    type="date"
                                                    value={editForm.birthDate}
                                                    onChange={(e) => setEditForm({ ...editForm, birthDate: e.target.value })}
                                                    className="w-full h-10 px-4 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:bg-white/10 transition-all [color-scheme:dark]"
                                                />
                                            </div>

                                            {/* Birth Time */}
                                            <div className="space-y-1 text-left">
                                                <label className="text-xs text-white/50 ml-1">태어난 시간</label>
                                                <input
                                                    type="time"
                                                    value={editForm.birthTime}
                                                    onChange={(e) => setEditForm({ ...editForm, birthTime: e.target.value })}
                                                    className="w-full h-10 px-4 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:bg-white/10 transition-all [color-scheme:dark]"
                                                />
                                            </div>
                                        </div>

                                        {/* Gender & Solar/Lunar Toggle */}
                                        <div className="flex items-center gap-4 py-2">
                                            <div className="flex bg-white/5 rounded-lg p-1 border border-white/10">
                                                <button
                                                    onClick={() => setEditForm({ ...editForm, gender: 'M' })}
                                                    className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${editForm.gender === 'M' ? 'bg-indigo-500 text-white shadow-lg' : 'text-white/40 hover:text-white/60'}`}
                                                >
                                                    남성
                                                </button>
                                                <button
                                                    onClick={() => setEditForm({ ...editForm, gender: 'F' })}
                                                    className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${editForm.gender === 'F' ? 'bg-indigo-500 text-white shadow-lg' : 'text-white/40 hover:text-white/60'}`}
                                                >
                                                    여성
                                                </button>
                                            </div>
                                            <div className="flex bg-white/5 rounded-lg p-1 border border-white/10">
                                                <button
                                                    onClick={() => setEditForm({ ...editForm, isSolar: true })}
                                                    className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${editForm.isSolar ? 'bg-indigo-500 text-white shadow-lg' : 'text-white/40 hover:text-white/60'}`}
                                                >
                                                    양력
                                                </button>
                                                <button
                                                    onClick={() => setEditForm({ ...editForm, isSolar: false })}
                                                    className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${!editForm.isSolar ? 'bg-indigo-500 text-white shadow-lg' : 'text-white/40 hover:text-white/60'}`}
                                                >
                                                    음력
                                                </button>
                                            </div>
                                        </div>

                                        <div className="flex gap-3 pt-2 justify-center md:justify-start">
                                            <button onClick={handleSave} className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-5 py-2 rounded-lg text-sm font-bold shadow-lg shadow-indigo-900/20 transition-all">
                                                <Save size={16} /> 저장
                                            </button>
                                            <button onClick={() => setIsEditing(false)} className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-5 py-2 rounded-lg text-sm font-bold transition-colors">
                                                <X size={16} /> 취소
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <div className="flex flex-col md:flex-row items-center gap-4 justify-center md:justify-start">
                                            <div className="flex items-baseline gap-3">
                                                <h2 className="text-3xl font-bold font-gmarket">{user.nameKor || '미입력'}</h2>

                                            </div>
                                            <button
                                                onClick={() => setIsEditing(true)}
                                                className="p-2 rounded-full hover:bg-white/10 text-white/40 hover:text-white transition-colors"
                                                title="정보 수정"
                                            >
                                                <Edit2 size={18} />
                                            </button>
                                        </div>

                                        <div className="flex flex-col md:flex-row items-center gap-6 justify-center md:justify-start">
                                            <div className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm">
                                                <span className="text-indigo-300 font-bold mr-2">닉네임</span>
                                                <span>{user.nickname || '미입력'}</span>
                                            </div>
                                            <div className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm">
                                                <span className="text-purple-300 font-bold mr-2">생년월일</span>
                                                <span>{user.birthDate ? `${user.birthDate} (${user.isSolar ? '양력' : '음력'})` : '미입력'}</span>
                                            </div>
                                            <div className="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm">
                                                <span className="text-pink-300 font-bold mr-2">성별</span>
                                                <span>{user.gender === 'M' ? '남성' : user.gender === 'F' ? '여성' : '미입력'}</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-4 justify-center md:justify-start pt-2 text-sm text-white/40 font-mono">
                                            <span className="flex items-center gap-1.5"><Mail size={14} /> {user.email}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* 2. Dashboard Section (Five Elements & Zodiac) */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                            {/* Five Elements */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 flex flex-col items-center justify-between aspect-square md:aspect-auto h-[320px] shadow-xl group hover:border-indigo-500/30 transition-all"
                            >
                                <div className="w-full flex justify-between items-center mb-2">
                                    <h3 className="text-lg font-bold font-gmarket text-indigo-300 flex items-center gap-2">
                                        <Orbit size={18} />
                                        오행(五行)
                                    </h3>
                                </div>
                                <ProfileRadarChart data={fiveElements} />
                                <div className="w-full flex justify-between px-2 pt-4">
                                    {fiveElements.map((e) => (
                                        <div key={e.name} className="flex flex-col items-center">
                                            <div className="w-1.5 h-1.5 rounded-full mb-1" style={{ backgroundColor: e.color }} />
                                            <span className="text-sm font-bold text-white/80">{e.hanja}</span>
                                            <span className="text-[10px] text-white/40 mt-1">{e.value}%</span>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>

                            {/* Zodiac Sign */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 flex flex-col items-center justify-center aspect-square md:aspect-auto h-[320px] shadow-xl relative overflow-hidden group hover:border-purple-500/30 transition-all"
                            >
                                {/* Pattern Background */}
                                <div className="absolute inset-0 opacity-10 pointer-events-none">
                                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-purple-500/20 via-transparent to-transparent" />
                                </div>

                                <div className="absolute top-6 left-6 flex flex-col">
                                    <h3 className="text-lg font-bold font-gmarket text-purple-300 flex items-center gap-2">
                                        <Sparkles size={18} />
                                        별자리
                                    </h3>
                                </div>

                                <div className="flex flex-col items-center justify-center mt-4">
                                    <motion.div
                                        animate={{
                                            y: [0, -10, 0],
                                        }}
                                        transition={{
                                            duration: 4,
                                            repeat: Infinity,
                                            ease: "easeInOut"
                                        }}
                                        className="text-8xl mb-4 drop-shadow-[0_0_30px_rgba(168,85,247,0.4)]"
                                    >
                                        {zodiac.icon}
                                    </motion.div>
                                    <div className="text-center">
                                        <span className="text-3xl font-bold font-gmarket tracking-wider text-white">
                                            {zodiac.name}
                                        </span>
                                    </div>
                                </div>
                            </motion.div>
                        </div>

                        {/* Re-enter Saju Button */}
                        <motion.button
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            onClick={() => navigate('/home', { state: { showSaju: true } })}
                            className="w-full py-4 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 hover:from-indigo-600/30 hover:to-purple-600/30 border border-white/10 rounded-2xl flex items-center justify-center gap-3 group transition-all"
                        >
                            <RefreshCcw size={18} className="text-indigo-400 group-hover:rotate-180 transition-transform duration-700" />
                            <span className="font-bold font-gmarket text-indigo-200">내 사주 정보 다시 입력하기</span>
                        </motion.button>



                        {/* 3. Settings & Danger Zone */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                            <div className="p-6 border-b border-white/5">
                                <h3 className="text-lg font-bold flex items-center gap-2">
                                    <User size={20} className="text-white/60" />
                                    계정 관리
                                </h3>
                            </div>

                            <div className="p-2">
                                <button
                                    onClick={() => setShowPasswordChangeModal(true)}
                                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 rounded-xl transition-colors group text-left"
                                >
                                    <span className="text-white/80 group-hover:text-white">비밀번호 변경하기</span>
                                    <Lock size={18} className="text-white/40 group-hover:text-white" />
                                </button>

                                <div className="my-1 border-t border-white/5" />

                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 rounded-xl transition-colors group text-left"
                                >
                                    <span className="text-white/80 group-hover:text-white">로그아웃</span>
                                    <LogOut size={18} className="text-white/40 group-hover:text-white" />
                                </button>

                                <div className="my-1 border-t border-white/5" />

                                <button
                                    onClick={() => setShowDeleteModal(true)}
                                    className="w-full flex items-center justify-between p-4 hover:bg-red-500/10 rounded-xl transition-colors group text-left"
                                >
                                    <span className="text-red-400 group-hover:text-red-300 font-medium">회원 탈퇴</span>
                                    <Trash2 size={18} className="text-red-400/60 group-hover:text-red-300" />
                                </button>
                            </div>
                        </div>

                    </div>
                </motion.div>
            ) : (
                <div className="w-full h-screen bg-[#0b0d14]" />
            )}
        </>
    );
};


export default MyPage;
