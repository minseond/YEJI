import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Mail, Lock, Smile, CheckCircle } from 'lucide-react';
import FortuneTeaserModal from '../features/FortuneTeaserModal';
import tarotCardImage from '../../assets/login_page/tarot.png';
import logoImage from '../../assets/logo.png';

import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import { login, signup, checkEmailDuplication, checkNicknameDuplication, sendEmailVerification, verifyEmail, getUserInfo } from '../../api/auth';
import Modal from '../common/Modal';
import { useCollection } from '../../contexts/CollectionContext';

const LoginPage = () => {
    const navigate = useNavigate();
    const { loadEquippedCharacters, loadMyCollections } = useCollection();
    const [isFortuneModalOpen, setIsFortuneModalOpen] = useState(false);
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    // Additional fields for Signup
    const [nickname, setNickname] = useState('');
    const [passwordConfirm, setPasswordConfirm] = useState('');

    // Verification States
    const [isEmailVerified, setIsEmailVerified] = useState(false);
    const [isCodeSent, setIsCodeSent] = useState(false);
    const [verificationCode, setVerificationCode] = useState('');
    const [timer, setTimer] = useState(0);

    // Validation States
    const [nicknameStatus, setNicknameStatus] = useState<'idle' | 'checking' | 'available' | 'duplicate' | 'error' | 'invalid'>('idle');
    const [nicknameMessage, setNicknameMessage] = useState('');
    const [passwordStatus, setPasswordStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');
    const [passwordMessage, setPasswordMessage] = useState('');
    const [emailStatus, setEmailStatus] = useState<'idle' | 'checking' | 'available' | 'duplicate' | 'error'>('idle');

    // Timer logic
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (timer > 0) {
            interval = setInterval(() => {
                setTimer((prev) => prev - 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [timer]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Debounce Logic for Nickname
    useEffect(() => {
        if (isLoginMode || !nickname.trim()) {
            setNicknameStatus('idle');
            setNicknameMessage('');
            return;
        }

        // 1. Character validation (Korean and English only)
        const hasKorean = /[가-힣]/.test(nickname);
        const hasInvalidChar = /[^a-zA-Z가-힣]/.test(nickname);

        if (hasInvalidChar) {
            setNicknameStatus('invalid');
            setNicknameMessage('한글과 영어만 사용 가능합니다.');
            return;
        }

        // 2. Length validation
        const maxLength = hasKorean ? 6 : 10;
        if (nickname.length > maxLength) {
            setNicknameStatus('invalid');
            setNicknameMessage(hasKorean ? '한글 포함 시 6자 이내로 입력해주세요.' : '영어만 사용 시 10자 이내로 입력해주세요.');
            return;
        }

        setNicknameStatus('checking');
        setNicknameMessage('');
        const timer = setTimeout(async () => {
            try {
                const isDuplicate = await checkNicknameDuplication(nickname);
                setNicknameStatus(isDuplicate ? 'duplicate' : 'available');
            } catch (error) {
                setNicknameStatus('error');
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [nickname, isLoginMode]);

    // Real-time validation for Password
    useEffect(() => {
        if (isLoginMode || !password) {
            setPasswordStatus('idle');
            setPasswordMessage('');
            return;
        }

        const minLength = 8;
        const hasLetter = /[a-zA-Z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        if (password.length < minLength) {
            setPasswordStatus('invalid');
            setPasswordMessage('최소 8자 이상의 비밀번호가 필요합니다.');
        } else if (!hasLetter || !hasNumber || !hasSpecial) {
            setPasswordStatus('invalid');
            setPasswordMessage('문자, 숫자, 특수문자를 각각 최소 1개씩 포함해야 합니다.');
        } else {
            setPasswordStatus('valid');
            setPasswordMessage('사용 가능한 비밀번호입니다.');
        }
    }, [password, isLoginMode]);

    // Debounce Logic for Email
    useEffect(() => {
        if (isLoginMode || !email.trim() || isEmailVerified) {
            setEmailStatus('idle');
            return;
        }
        // Basic pattern check before API call
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email)) {
            setEmailStatus('error'); // weak validation reuse
            return;
        }

        setEmailStatus('checking');
        const timer = setTimeout(async () => {
            try {
                const isDuplicate = await checkEmailDuplication(email);
                setEmailStatus(isDuplicate ? 'duplicate' : 'available');
            } catch (error) {
                setEmailStatus('error');
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [email, isLoginMode, isEmailVerified]);

    // Helper to render status message
    const renderStatusMessage = (status: string, type: 'nickname' | 'email' | 'password') => {
        if (status === 'checking') return <span className="text-xs text-white/40 ml-2">확인 중...</span>;
        if (status === 'available') return <span className="text-xs text-green-400 ml-2">사용 가능한 {type === 'nickname' ? '닉네임' : '이메일'}입니다.</span>;
        if (status === 'duplicate') return <span className="text-xs text-red-400 ml-2">이미 사용 중인 {type === 'nickname' ? '닉네임' : '이메일'}입니다.</span>;
        if (status === 'invalid' && type === 'nickname') return <span className="text-xs text-red-400 ml-2">{nicknameMessage}</span>;
        if (status === 'invalid' && type === 'password') return <span className="text-xs text-red-400 ml-2">{passwordMessage}</span>;
        if (status === 'valid' && type === 'password') return <span className="text-xs text-green-400 ml-2">{passwordMessage}</span>;
        if (status === 'error' && type === 'email' && email.trim()) return <span className="text-xs text-red-400 ml-2">이메일 형식이 올바르지 않습니다.</span>;
        return null;
    };

    // Modal State
    const [alertModal, setAlertModal] = useState({
        isOpen: false,
        title: '',
        message: '',
        type: 'info' as 'error' | 'success' | 'info',
        onConfirm: undefined as (() => void) | undefined
    });

    const showAlert = (title: string, message: string, type: 'error' | 'success' | 'info' = 'info', onConfirm?: () => void) => {
        setAlertModal({ isOpen: true, title, message, type, onConfirm });
    };

    const handleSendCode = async () => {
        if (!email.trim() || emailStatus !== 'available') {
            showAlert('입력 오류', '사용 가능한 이메일을 입력해주세요.', 'error');
            return;
        }

        try {
            await sendEmailVerification(email);
            setIsCodeSent(true);
            setTimer(300); // 5 minutes
            showAlert('발송 성공', '인증 코드가 이메일로 발송되었습니다.', 'success');
        } catch (error: any) {
            showAlert('발송 실패', error.response?.data?.message || '인증 코드 발송 중 오류가 발생했습니다.', 'error');
        }
    };

    const handleVerifyCode = async () => {
        if (!verificationCode.trim()) {
            showAlert('입력 오류', '인증 코드를 입력해주세요.', 'error');
            return;
        }

        try {
            const isSuccess = await verifyEmail({ email, code: verificationCode });
            if (isSuccess) {
                setIsEmailVerified(true);
                setIsCodeSent(false); // Hide code input after success
                setTimer(0);
                showAlert('인증 성공', '이메일 인증이 완료되었습니다.', 'success');
            } else {
                showAlert('인증 실패', '인증 코드가 올바르지 않습니다.', 'error');
            }
        } catch (error: any) {
            showAlert('인증 실패', error.response?.data?.message || '인증 코드 검증 중 오류가 발생했습니다.', 'error');
        }
    };

    const handleAuthAction = async () => {
        // Validation Logic
        if (!email.trim() || !password.trim()) {
            showAlert('입력 오류', '이메일과 비밀번호를 모두 입력해주세요.', 'error');
            return;
        }

        if (!isLoginMode) {
            // Signup Logic
            if (!isEmailVerified) {
                showAlert('인증 필요', '이메일 인증을 완료해주세요.', 'error');
                return;
            }
            if (!nickname.trim()) {
                showAlert('입력 오류', '닉네임을 입력해주세요.', 'error');
                return;
            }
            if (password !== passwordConfirm) {
                showAlert('입력 오류', '비밀번호가 일치하지 않습니다.', 'error');
                return;
            }

            if (nicknameStatus === 'duplicate') {
                showAlert('입력 오류', '이미 사용 중인 닉네임입니다.', 'error');
                return;
            }
            if (nicknameStatus === 'invalid') {
                showAlert('입력 오류', nicknameMessage, 'error');
                return;
            }
            if (passwordStatus === 'invalid') {
                showAlert('입력 오류', passwordMessage, 'error');
                return;
            }
            if (emailStatus === 'duplicate') {
                showAlert('입력 오류', '이미 사용 중인 이메일입니다.', 'error');
                return;
            }

            try {
                await signup({ email, password, nickname });

                // Auto Login Sequence
                try {
                    const response = await login({ email, password });

                    // Store tokens
                    localStorage.setItem('accessToken', response.accessToken);
                    localStorage.setItem('refreshToken', response.refreshToken);

                    // Get user info and load context
                    const decoded: any = jwtDecode(response.accessToken);
                    const userId = decoded.userId;
                    const userInfo = await getUserInfo(userId);
                    localStorage.setItem('userId', userInfo.id.toString());

                    loadEquippedCharacters(userInfo.id);
                    loadMyCollections();

                    showAlert('가입 완료', '서비스 이용을 원활하게 하기 위해\n사주 정보를 입력해야 합니다.', 'success', () => {
                        navigate('/home', { state: { showSaju: true } });
                    });
                } catch (loginError) {
                    console.error("Auto Login Failed:", loginError);
                    // Fallback to manual login
                    showAlert('회원가입 성공', '회원가입이 완료되었습니다!\n로그인을 진행해주세요.', 'success', () => {
                        setIsLoginMode(true);
                        setPassword('');
                        setPasswordConfirm('');
                        setNickname('');
                        setNicknameStatus('idle');
                        setEmailStatus('idle');
                    });
                }

            } catch (error: any) {
                console.error("Signup Failed:", error);
                const errorMsg = error.response?.data?.message || "회원가입 중 오류가 발생했습니다.";
                showAlert('가입 실패', errorMsg, 'error');
            }
        } else {
            // Proceed with Login
            try {
                const response = await login({ email, password });

                // Store tokens
                localStorage.setItem('accessToken', response.accessToken);
                localStorage.setItem('refreshToken', response.refreshToken);

                // Get user info to retrieve userId and equipped characters
                try {
                    const decoded: any = jwtDecode(response.accessToken);
                    const userId = decoded.userId;

                    if (!userId) throw new Error('No userId in token');

                    const userInfo = await getUserInfo(userId);
                    localStorage.setItem('userId', userInfo.id.toString());

                    // Load equipped characters via context
                    loadEquippedCharacters(userInfo.id);
                    loadMyCollections();
                } catch (userInfoError) {
                    console.error('Failed to load user info:', userInfoError);
                }

                // Navigate to home
                navigate('/home');
            } catch (error: any) {
                console.error('Login Failed detailed:', error);
                const errorMessage = error.response?.data?.message || '아이디 또는 비밀번호를 확인해주세요.';
                const statusCode = error.response?.status;
                showAlert('로그인 실패', `${errorMessage} (Code: ${statusCode || 'Unknown'})`, 'error');
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleAuthAction();
        }
    };


    return (
        <div className="relative min-h-screen w-full overflow-hidden font-['Pretendard'] text-white bg-black">
            {/* Background Image: Flipped */}
            <div
                className="absolute inset-0 bg-[url('/assets/bg/fortune_bg_oriental.png')] bg-cover bg-center scale-x-[-1] z-0 opacity-100"
            />

            <div className="relative z-10 flex flex-row w-full min-h-screen">
                {/* LEFT PANEL: Login Interface (45%) */}
                <div className="w-[45%] h-screen overflow-y-auto relative z-50 bg-black/40 backdrop-blur-xl border-r border-white/10 scrollbar-hide">
                    <div className="flex flex-col min-h-full p-8 lg:p-16 pb-10 lg:pb-32 justify-center">
                        {/* Header / Logo */}
                        <div className="flex items-center gap-4 mb-10 w-full max-w-md mx-auto">
                            <img src={logoImage} alt="YEJI Logo" className="w-14 h-14 rounded-full object-cover opacity-90 shadow-lg shadow-indigo-500/20" />
                            <span className="text-4xl font-bold tracking-widest font-gmarket text-white">YEJI</span>
                        </div>

                        {/* Center Content Wrapper */}
                        <div className="flex flex-col justify-center">
                            <div className="max-w-md w-full mx-auto space-y-8">
                                <div className="space-y-3">
                                    <h1 className="text-3xl lg:text-4xl font-bold leading-tight font-gmarket text-white">
                                        {isLoginMode ? '운명이 당신을 기다리고 있어요.' : '새로운 운명을 시작하세요.'}
                                    </h1>
                                    <p className="text-white/50 text-base font-light">
                                        {isLoginMode ? '당신의 여정을 계속 이어가세요.' : '당신만의 특별한 이야기를 만들어보세요.'}
                                    </p>
                                </div>

                                {/* Local Login/Signup Form */}
                                <div className="space-y-5">
                                    <AnimatePresence mode="wait">
                                        {!isLoginMode && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="space-y-4 overflow-hidden"
                                            >
                                                <div className="space-y-1.5">
                                                    <div className="flex justify-between items-center">
                                                        <label className="text-xs font-medium text-white/60 ml-1">닉네임</label>
                                                        {renderStatusMessage(nicknameStatus, 'nickname')}
                                                    </div>
                                                    <div className="relative">
                                                        <Smile className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                                                        <input
                                                            type="text"
                                                            value={nickname}
                                                            onChange={(e) => setNickname(e.target.value)}
                                                            placeholder="운명적인 별명"
                                                            className={`w-full h-12 pl-12 pr-4 bg-white/5 border ${nicknameStatus === 'duplicate' || nicknameStatus === 'invalid' ? 'border-red-500/50' : nicknameStatus === 'available' ? 'border-green-500/50' : 'border-white/10'} rounded-xl text-sm text-white focus:outline-none focus:bg-white/10 transition-all placeholder:text-white/20`}
                                                        />
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    <div className="space-y-1.5">
                                        <div className="flex justify-between items-center">
                                            <label className="text-xs font-medium text-white/60 ml-1">이메일</label>
                                            {!isLoginMode && renderStatusMessage(emailStatus, 'email')}
                                        </div>
                                        <div className="flex gap-2">
                                            <div className="relative flex-1">
                                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                                                <input
                                                    type="email"
                                                    value={email}
                                                    onChange={(e) => setEmail(e.target.value)}
                                                    onKeyDown={handleKeyDown}
                                                    readOnly={!isLoginMode && isEmailVerified}
                                                    placeholder="example@email.com"
                                                    className={`w-full h-12 pl-12 pr-4 bg-white/5 border ${(!isLoginMode && isEmailVerified) ? 'border-green-500/50 opacity-60' : (!isLoginMode && emailStatus === 'duplicate') ? 'border-red-500/50' : (!isLoginMode && emailStatus === 'available') ? 'border-green-500/50' : 'border-white/10'} rounded-xl text-sm text-white focus:outline-none focus:bg-white/10 transition-all placeholder:text-white/20`}
                                                />
                                                {!isLoginMode && isEmailVerified && (
                                                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-green-400">
                                                        <CheckCircle size={18} />
                                                    </div>
                                                )}
                                            </div>
                                            {!isLoginMode && !isEmailVerified && (
                                                <button
                                                    onClick={handleSendCode}
                                                    disabled={emailStatus !== 'available' || (isCodeSent && timer > 0)}
                                                    className="px-4 h-12 rounded-xl bg-white/10 border border-white/20 text-xs font-bold text-white hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all whitespace-nowrap shadow-sm"
                                                >
                                                    {isCodeSent ? '재발송' : '인증발송'}
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    <AnimatePresence>
                                        {!isLoginMode && isCodeSent && !isEmailVerified && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="space-y-1.5 overflow-hidden"
                                            >
                                                <div className="flex justify-between items-center">
                                                    <label className="text-xs text-white/50 ml-1">인증번호</label>
                                                    <span className="text-xs text-amber-400 font-mono">{formatTime(timer)}</span>
                                                </div>
                                                <div className="flex gap-2">
                                                    <div className="relative flex-1">
                                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                                                        <input
                                                            type="text"
                                                            value={verificationCode}
                                                            onChange={(e) => setVerificationCode(e.target.value)}
                                                            placeholder="6자리 숫자"
                                                            maxLength={6}
                                                            className="w-full h-12 pl-12 pr-4 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:bg-white/10 transition-all placeholder:text-white/20"
                                                        />
                                                    </div>
                                                    <button
                                                        onClick={handleVerifyCode}
                                                        className="px-5 h-12 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white transition-all shadow-lg shadow-indigo-900/40"
                                                    >
                                                        확인
                                                    </button>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    <div className="space-y-1.5">
                                        <div className="flex justify-between items-center">
                                            <label className="text-xs font-medium text-white/60 ml-1">비밀번호</label>
                                            {!isLoginMode && renderStatusMessage(passwordStatus, 'password')}
                                        </div>
                                        <div className="relative">
                                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                                            <input
                                                type="password"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                onKeyDown={handleKeyDown}
                                                placeholder="••••••••"
                                                className={`w-full h-12 pl-12 pr-4 bg-white/5 border ${!isLoginMode && passwordStatus === 'invalid' ? 'border-red-500/50' : !isLoginMode && passwordStatus === 'valid' ? 'border-green-500/50' : 'border-white/10'} rounded-xl text-sm text-white focus:outline-none focus:bg-white/10 transition-all placeholder:text-white/20`}
                                            />
                                        </div>
                                    </div>

                                    <AnimatePresence mode="wait">
                                        {!isLoginMode && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="space-y-1.5 overflow-hidden"
                                            >
                                                <label className="text-xs font-medium text-white/60 ml-1">비밀번호 확인</label>
                                                <div className="relative">
                                                    <CheckCircle className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
                                                    <input
                                                        type="password"
                                                        value={passwordConfirm}
                                                        onChange={(e) => setPasswordConfirm(e.target.value)}
                                                        onKeyDown={handleKeyDown}
                                                        placeholder="••••••••"
                                                        className="w-full h-12 pl-12 pr-4 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:bg-white/10 transition-all placeholder:text-white/20"
                                                    />
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    <motion.button
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={handleAuthAction}
                                        className="w-full h-12 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-base shadow-xl shadow-indigo-900/30 transition-all flex items-center justify-center gap-2 mt-4"
                                    >
                                        {isLoginMode ? '로그인' : '회원가입'}
                                        <ArrowRight size={20} />
                                    </motion.button>

                                    <div className="flex justify-center text-sm text-white/40 gap-2 pt-2">
                                        <span>{isLoginMode ? '계정이 없으신가요?' : '이미 계정이 있으신가요?'}</span>
                                        <button
                                            onClick={() => {
                                                setIsLoginMode(!isLoginMode);
                                                setPassword('');
                                                setPasswordConfirm('');
                                                setIsEmailVerified(false);
                                                setIsCodeSent(false);
                                                setVerificationCode('');
                                                setTimer(0);
                                            }}
                                            className="text-indigo-400 hover:text-indigo-300 font-bold underline underline-offset-4 transition-colors"
                                        >
                                            {isLoginMode ? '회원가입' : '로그인'}
                                        </button>
                                    </div>
                                </div>


                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL: Visual Identity (55%) */}
                <div className="flex w-[55%] h-screen relative z-10 items-center justify-center overflow-hidden bg-black/20">
                    {/* Dynamic Background Blobs */}
                    <div className="absolute inset-0 pointer-events-none">
                        <div className="absolute top-[-10%] right-[-10%] w-[70%] h-[70%] bg-indigo-600/30 rounded-full blur-[150px] animate-pulse" />
                        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] bg-purple-600/20 rounded-full blur-[120px]" />
                    </div>

                    {/* Main Card Visualization - High Contrast */}
                    <div className="relative z-40 w-full flex justify-center px-12">
                        <motion.div
                            initial={{ opacity: 1, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8 }}
                            className="relative w-full max-w-[480px] aspect-[4/5] z-50"
                        >
                            {/* Interactive Card */}
                            <div
                                onClick={() => setIsFortuneModalOpen(true)}
                                className="group absolute inset-0 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-3xl rounded-[40px] border-2 border-white/20 shadow-[0_0_50px_rgba(79,70,229,0.3)] overflow-hidden flex flex-col cursor-pointer hover:border-white/40 transition-all duration-500"
                            >
                                <div className="flex-1 p-8 flex flex-col items-center justify-center space-y-10">
                                    {/* Tarot Image Container */}
                                    <div className="w-[55%] relative rounded-2xl shadow-2xl shadow-black/50 overflow-hidden border border-white/10">
                                        <img
                                            src={tarotCardImage}
                                            alt="Tarot"
                                            className="w-full h-auto object-cover transition-transform duration-700"
                                        />
                                        {/* Shine Effect */}
                                        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/60 to-transparent opacity-0 -translate-x-full group-hover:animate-shimmer group-hover:opacity-100 block" style={{ transform: 'skewX(-25deg)' }} />
                                    </div>

                                    <div className="text-center space-y-4">
                                        <h3 className="text-4xl font-bold font-gmarket text-white drop-shadow-lg">간단 카드운세</h3>
                                        <p className="text-white/70 text-lg font-light">로그인 없이 오늘의 운세를 확인하세요</p>
                                    </div>

                                    <div className="px-10 py-4 rounded-full bg-indigo-600 text-white font-bold text-lg shadow-lg shadow-indigo-900/50 flex items-center gap-3">
                                        <span>카드 뽑아보기</span>
                                        <ArrowRight size={20} />
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Big Typography Overlay - Increased Opacity */}
                    <div className="absolute bottom-16 right-16 text-right z-0 pointer-events-none opacity-20">
                        <h2 className="text-[120px] font-bold font-gmarket text-white leading-none">YEJI</h2>
                        <p className="text-white text-2xl tracking-[1em] mr-4 uppercase">Destiny</p>
                    </div>
                </div>
            </div>

            {/* Modals */}
            <FortuneTeaserModal
                isOpen={isFortuneModalOpen}
                onClose={() => setIsFortuneModalOpen(false)}
            />
            <Modal
                isOpen={alertModal.isOpen}
                onClose={() => setAlertModal(prev => ({ ...prev, isOpen: false }))}
                title={alertModal.title}
                message={alertModal.message}
                type={alertModal.type}
                onConfirm={alertModal.onConfirm}
            />
        </div>
    );
};



export default LoginPage;
