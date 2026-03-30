import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, AlertCircle, Mail, Timer, Trash2 } from 'lucide-react';
import { sendWithdrawVerification, withdrawUser } from '../../api/auth';

interface AccountDeleteModalProps {
    isOpen: boolean;
    onClose: () => void;
    email: string;
    onSuccess: () => void;
}

const AccountDeleteModal = ({ isOpen, onClose, email, onSuccess }: AccountDeleteModalProps) => {
    const [step, setStep] = useState<1 | 2>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Step 2: Verification Code
    const [code, setCode] = useState('');
    const [timeLeft, setTimeLeft] = useState(0);

    useEffect(() => {
        if (isOpen) {
            setStep(1);
            setCode('');
            setError('');
            setTimeLeft(0);
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
            await sendWithdrawVerification();
            setStep(2);
            setTimeLeft(300); // 5 minutes
        } catch (err: any) {
            setError(err.response?.data?.message || '인증번호 전송에 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleWithdraw = async () => {
        if (loading || !code) return;
        setLoading(true);
        setError('');
        try {
            await withdrawUser(code);
            onSuccess(); // Parent handles logout and redirect
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.message || '회원 탈퇴에 실패했습니다. (인증번호를 확인해주세요)');
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
                    className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[150] flex items-center justify-center p-4"
                    onClick={onClose}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.9, opacity: 0, y: 20 }}
                        className="w-full max-w-sm rounded-2xl bg-[#0b0d14] border border-red-500/30 shadow-2xl overflow-hidden relative"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Header */}
                        <div className="p-6 pb-4 flex items-center justify-between border-b border-red-500/10">
                            <h3 className="text-lg font-bold text-red-500 flex items-center gap-2">
                                <AlertTriangle size={20} className="fill-red-500/10" />
                                회원 탈퇴
                            </h3>
                            <button onClick={onClose} className="text-white/50 hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Body */}
                        <div className="p-6 space-y-6">
                            {step === 1 && (
                                <div className="space-y-4">
                                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl space-y-2">
                                        <p className="text-red-200 text-sm font-bold">⚠️ 경고: 모든 데이터가 삭제됩니다.</p>
                                        <p className="text-red-200/60 text-xs leading-relaxed">
                                            포인트, 운세 기록, 도감 등 모든 활동 내역이 즉시 삭제되며 복구할 수 없습니다.
                                            정말 탈퇴하시려면 이메일 인증이 필요합니다.
                                        </p>
                                    </div>

                                    <div className="text-center py-2">
                                        <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-2">
                                            <Mail size={24} className="text-white/60" />
                                        </div>
                                        <p className="text-sm text-white/80">{email}</p>
                                        <p className="text-xs text-white/40">위 이메일로 인증 코드를 발송합니다.</p>
                                    </div>

                                    <button
                                        onClick={handleSendCode}
                                        disabled={loading}
                                        className="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold transition-all shadow-lg shadow-red-900/20"
                                    >
                                        {loading ? '전송 중...' : '인증코드 전송하기'}
                                    </button>
                                </div>
                            )}

                            {step === 2 && (
                                <div className="space-y-4">
                                    <div className="space-y-1">
                                        <label className="text-xs text-red-400/80 ml-1">인증코드 입력</label>
                                        <div className="relative">
                                            <input
                                                type="text"
                                                value={code}
                                                onChange={(e) => setCode(e.target.value)}
                                                className="w-full h-12 px-4 bg-black/30 border border-red-500/30 rounded-xl text-white focus:outline-none focus:border-red-500 transition-all font-mono tracking-widest text-center text-lg"
                                                placeholder="000000"
                                                maxLength={6}
                                            />
                                            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-xs text-red-300 font-mono">
                                                <Timer size={12} />
                                                <span>{formatTime(timeLeft)}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleWithdraw}
                                        disabled={loading || !code || timeLeft === 0}
                                        className="w-full py-3 rounded-xl bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-bold transition-all shadow-lg shadow-red-900/20 flex items-center justify-center gap-2"
                                    >
                                        <Trash2 size={18} />
                                        {loading ? '처리 중...' : '회원 탈퇴 확정'}
                                    </button>

                                    <button
                                        onClick={() => setStep(1)} // Or resend logic
                                        className="w-full text-xs text-white/40 hover:text-white transition-colors"
                                    >
                                        이전으로 돌아가기
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

export default AccountDeleteModal;
