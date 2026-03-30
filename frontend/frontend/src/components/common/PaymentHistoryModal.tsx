
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Receipt, Calendar, CreditCard, AlertCircle } from 'lucide-react';
import { fetchPaymentHistory, type PaymentHistory } from '../../api/shop';

interface PaymentHistoryModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const PaymentHistoryModal = ({ isOpen, onClose }: PaymentHistoryModalProps) => {
    const [history, setHistory] = useState<PaymentHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadHistory();
        }
    }, [isOpen]);

    const loadHistory = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await fetchPaymentHistory();

            // [Frontend Test] Merge Local Test Payments
            const localData = JSON.parse(localStorage.getItem('local_test_payments') || '[]');
            const merged = [...localData, ...data];

            // Filter: PAID or CANCELLED only
            const filtered = merged.filter(item =>
                ['PAID', 'CANCELLED'].includes(item.status)
            );

            // 최신순 정렬
            const sorted = filtered.sort((a, b) =>
                new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
            );
            setHistory(sorted);
        } catch (err) {
            console.error("Failed to load payment history:", err);
            setError("결제 내역을 불러오는데 실패했습니다.");
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'PAID':
                return <span className="bg-green-500/20 text-green-400 text-xs px-2 py-1 rounded-full font-bold">결제 완료</span>;
            case 'PENDING':
                return <span className="bg-yellow-500/20 text-yellow-400 text-xs px-2 py-1 rounded-full font-bold">대기 중</span>;
            case 'CANCELLED':
                return <span className="bg-red-500/20 text-red-400 text-xs px-2 py-1 rounded-full font-bold">취소됨</span>;
            case 'FAILED':
                return <span className="bg-red-500/20 text-red-400 text-xs px-2 py-1 rounded-full font-bold">실패</span>;
            default:
                return <span className="bg-gray-500/20 text-gray-400 text-xs px-2 py-1 rounded-full">{status}</span>;
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 overflow-hidden"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
                    >
                        <div className="bg-[#1a1a2e] border border-white/10 rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl pointer-events-auto">

                            {/* Header */}
                            <div className="p-5 border-b border-white/10 flex items-center justify-between">
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Receipt className="text-indigo-400" size={24} />
                                    결제 내역
                                </h3>
                                <button
                                    onClick={onClose}
                                    className="p-1 rounded-full hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                                {loading ? (
                                    <div className="flex flex-col items-center justify-center py-12 text-white/40 gap-3">
                                        <div className="w-8 h-8 border-2 border-white/20 border-t-indigo-500 rounded-full animate-spin" />
                                        <span className="text-sm">내역을 불러오는 중...</span>
                                    </div>
                                ) : error ? (
                                    <div className="flex flex-col items-center justify-center py-12 text-red-400 gap-3">
                                        <AlertCircle size={32} />
                                        <span>{error}</span>
                                        <button
                                            onClick={loadHistory}
                                            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white mt-2"
                                        >
                                            다시 시도
                                        </button>
                                    </div>
                                ) : history.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center py-16 text-white/30 gap-4">
                                        <Receipt size={48} className="opacity-50" />
                                        <p>아직 결제 내역이 없습니다.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {history.map((platform) => (
                                            <div
                                                key={platform.orderId}
                                                className="bg-white/5 border border-white/5 rounded-xl p-4 hover:bg-white/10 transition-colors"
                                            >
                                                <div className="flex items-start justify-between mb-2">
                                                    <div>
                                                        <span className="text-sm text-indigo-300 font-bold mb-1 block">
                                                            {platform.productName}
                                                        </span>
                                                        <div className="flex items-center gap-2 text-xs text-white/40">
                                                            <Calendar size={12} />
                                                            {formatDate(platform.createdAt)}
                                                        </div>
                                                    </div>
                                                    {getStatusBadge(platform.status)}
                                                </div>

                                                <div className="flex items-center justify-between pt-2 border-t border-white/5 mt-2">
                                                    <div className="flex items-center gap-2 text-xs text-white/50 font-mono">
                                                        <CreditCard size={12} />
                                                        {platform.orderId}
                                                    </div>
                                                    <span className="text-white font-bold">
                                                        {platform.amount.toLocaleString()}원
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default PaymentHistoryModal;
