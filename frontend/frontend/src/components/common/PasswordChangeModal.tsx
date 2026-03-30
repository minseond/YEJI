
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, X, AlertCircle, Mail, Timer } from 'lucide-react';
import { sendEmailVerification, verifyEmail, resetPassword } from '../../api/auth';

interface PasswordChangeModalProps {
    isOpen: boolean;
    onClose: () => void;
    email: string;
    onSuccess: () => void;
}

const PasswordChangeModal = ({ isOpen, onClose, email, onSuccess }: PasswordChangeModalProps) => {
    const [step, setStep] = useState<1 | 2 | 3>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Step 2: Verification Code
    const [code, setCode] = useState('');
    const [timeLeft, setTimeLeft] = useState(0);

    // Step 3: New Password
    const [newPassword, setNewPassword] = useState('');
    const [newPasswordConfirm, setNewPasswordConfirm] = useState('');

    useEffect(() => {
        if (isOpen) {
            setStep(1);
            setCode('');
            setNewPassword('');
            setNewPasswordConfirm('');
            setError('');
        }
    }, [isOpen]);

    useEffect(() => {
        let timer: NodeJS.Timeout;
        if (timeLeft > 0) {
            timer = setInterval(() => {
                setTimeLeft((prev) => prev - 1);
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [timeLeft]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleSendCode = async () => {
        if (loading) return;
        setLoading(true);
        setError('');
        try {
            await sendEmailVerification(email);
            setStep(2);
            setTimeLeft(300); // 5 minutes
        } catch (err: any) {
            setError(err.response?.data?.message || '인증번호 전송에 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyCode = async () => {
        if (loading || !code) return;
        setLoading(true);
        setError('');
        try {
            const isValid = await verifyEmail({ email, code });
            if (isValid) {
                setStep(3);
            } else {
                setError('인증번호가 올바르지 않습니다.');
            }
        } catch (err: any) {
            setError(err.response?.data?.message || '인증번호 검증에 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async () => {
        if (loading || !newPassword) return;
        if (newPassword !== newPasswordConfirm) {
            setError('비밀번호가 일치하지 않습니다.');
            return;
        }
        setLoading(true);
        setError('');
        try {
            await resetPassword({ email, code, newPassword });
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.message || '비밀번호 변경에 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.9, opacity: 0, y: 20 }}
                        className="w-full max-w-sm rounded-2xl bg-gradient-to-br from-indigo-900/90 to-purple-900/90 border border-white/20 shadow-2xl overflow-hidden relative"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="p-6 pb-4 flex items-center justify-between border-b border-white/10">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Lock size={20} className="text-indigo-400" />
                                비밀번호 변경
                            </h3>
                            <button onClick={onClose} className="text-white/50 hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 space-y-6">
                            {/* Steps Indicator */}
                            <div className="flex items-center justify-center gap-2">
                                {[1, 2, 3].map((s) => (
                                    <div
                                        key={s}
                                        className={`w-2.5 h-2.5 rounded-full transition-all ${step === s ? 'bg-indigo-400 scale-125' :
                                            step > s ? 'bg-indigo-600' : 'bg-white/10'
                                            }`}
                                    />
                                ))}
                            </div>

                            {/* Verification Sending */}
                            {step === 1 && (
                                <div className="space-y-4 text-center">
                                    <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto">
                                        <Mail size={32} className="text-indigo-300" />
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-white font-medium">{email}</p>
                                        <p className="text-xs text-white/50">
                                            위 이메일로 인증번호를 전송합니다.
                                        </p>
                                    </div>
                                    <button
                                        onClick={handleSendCode}
                                        disabled={loading}
                                        className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold transition-all shadow-lg shadow-indigo-900/30"
                                    >
                                        {loading ? '전송 중...' : '인증번호 전송'}
                                    </button>
                                </div>
                            )}

                            {/* Verification Input */}
                            {step === 2 && (
                                <div className="space-y-4">
                                    <div className="space-y-1">
                                        <label className="text-xs text-white/50 ml-1">인증번호</label>
                                        <div className="relative">
                                            <input
                                                type="text"
                                                value={code}
                                                onChange={(e) => setCode(e.target.value)}
                                                className="w-full h-12 px-4 bg-black/30 border border-white/10 rounded-xl text-white focus:outline-none focus:border-indigo-500 transition-all font-mono tracking-widest text-center text-lg"
                                                placeholder="000000"
                                                maxLength={6}
                                            />
                                            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-xs text-indigo-300 font-mono">
                                                <Timer size={12} />
                                                <span>{formatTime(timeLeft)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleVerifyCode}
                                        disabled={loading || !code || timeLeft === 0}
                                        className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold transition-all shadow-lg shadow-indigo-900/30"
                                    >
                                        {loading ? '확인 중...' : '인증번호 확인'}
                                    </button>
                                    <button
                                        onClick={handleSendCode}
                                        className="w-full text-xs text-white/40 hover:text-white transition-colors"
                                    >
                                        인증번호가 오지 않나요? 다시 보내기
                                    </button>
                                </div>
                            )}

                            {/* New Password Input */}
                            {step === 3 && (
                                <div className="space-y-4">
                                    <div className="space-y-1">
                                        <label className="text-xs text-white/50 ml-1">새 비밀번호</label>
                                        <input
                                            type="password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            className="w-full h-12 px-4 bg-black/30 border border-white/10 rounded-xl text-white focus:outline-none focus:border-indigo-500 transition-all"
                                            placeholder="비밀번호를 입력하세요"
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-white/50 ml-1">비밀번호 확인</label>
                                        <input
                                            type="password"
                                            value={newPasswordConfirm}
                                            onChange={(e) => setNewPasswordConfirm(e.target.value)}
                                            className="w-full h-12 px-4 bg-black/30 border border-white/10 rounded-xl text-white focus:outline-none focus:border-indigo-500 transition-all"
                                            placeholder="한 번 더 입력하세요"
                                        />
                                    </div>
                                    <button
                                        onClick={handleResetPassword}
                                        disabled={loading || !newPassword || !newPasswordConfirm}
                                        className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold transition-all shadow-lg shadow-indigo-900/30"
                                    >
                                        {loading ? '변경 중...' : '비밀번호 변경하기'}
                                    </button>
                                </div>
                            )}

                            {/* Error Message */}
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-400 text-xs"
                                >
                                    <AlertCircle size={14} className="shrink-0" />
                                    <span>{error}</span>
                                </motion.div>
                            )}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default PasswordChangeModal;
