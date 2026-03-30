import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    message: string;
    type?: 'error' | 'success' | 'info';
    onConfirm?: () => void;
    showCancel?: boolean;
    cancelText?: string;
    confirmText?: string;
    onCancel?: () => void;
}

const Modal = ({
    isOpen,
    onClose,
    title,
    message,
    type = 'info',
    onConfirm,
    showCancel = false,
    cancelText = '취소',
    confirmText = '확인',
    onCancel
}: ModalProps) => {
    const getIcon = () => {
        switch (type) {
            case 'error': return <AlertCircle className="text-purple-400" size={32} />;
            case 'success': return <CheckCircle className="text-green-400" size={32} />;
            default: return <Info className="text-blue-400" size={32} />;
        }
    };

    const getGradient = () => {
        switch (type) {
            case 'error': return 'from-purple-500/20 to-indigo-500/20';
            case 'success': return 'from-green-500/20 to-emerald-500/20';
            default: return 'from-blue-500/20 to-indigo-500/20';
        }
    };

    const handleConfirm = () => {
        if (onConfirm) {
            onConfirm();
        }
        onClose();
    };

    const handleCancel = () => {
        if (onCancel) {
            onCancel();
        }
        onClose();
    };

    // Handle Enter key for confirmation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (isOpen && e.key === 'Enter') {
                e.preventDefault();
                handleConfirm();
            }
        };

        if (isOpen) {
            window.addEventListener('keydown', handleKeyDown);
        }
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onConfirm, onClose]); // Dependencies include handleConfirm's dependencies effectively


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
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
                    >
                        {/* Modal Content */}
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0, y: 20 }}
                            animate={{ scale: 1, opacity: 1, y: 0 }}
                            exit={{ scale: 0.9, opacity: 0, y: 20 }}
                            onClick={(e) => e.stopPropagation()}
                            className={`w-full max-w-sm rounded-2xl bg-gradient-to-br ${getGradient()} border border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden relative`}
                        >
                            {/* Header */}
                            <div className="p-6 pb-4 flex items-center gap-4 border-b border-white/5">
                                {getIcon()}
                                <h3 className="text-lg font-bold text-white font-gmarket flex-1">{title}</h3>
                                <button
                                    onClick={onClose}
                                    className="p-1 rounded-full hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Body */}
                            <div className="p-6 pt-4 text-white/80 font-light leading-relaxed">
                                {message}
                            </div>

                            {/* Footer (Optional Action) */}
                            <div className="p-6 pt-0 flex justify-end gap-3">
                                {showCancel && (
                                    <button
                                        onClick={handleCancel}
                                        className="px-6 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 text-sm font-medium transition-colors"
                                    >
                                        {cancelText}
                                    </button>
                                )}
                                <button
                                    onClick={handleConfirm}
                                    className="px-6 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-colors"
                                >
                                    {confirmText}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default Modal;
