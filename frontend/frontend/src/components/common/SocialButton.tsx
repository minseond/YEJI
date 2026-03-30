import { motion } from 'framer-motion';

interface SocialButtonProps {
    icon: 'kakao' | 'naver' | 'google';
    label: string;
    bgColor: string;
    textColor: string;
    onClick: () => void;
    delay?: number;
    className?: string;
}

const SocialButton = ({ icon, label, bgColor, textColor, onClick, delay = 0, className = '' }: SocialButtonProps) => {
    const getIcon = (name: string) => {
        switch (name) {
            case 'kakao': return <img src="/assets/logos/kakao.svg" alt="Kakao" className="w-5 h-5 block" />;
            case 'naver': return <img src="/assets/logos/naver.svg" alt="Naver" className="w-4 h-4 block" />;
            case 'google': return <img src="/assets/logos/google.svg" alt="Google" className="w-5 h-5 block" />;
            default: return null;
        }
    };

    return (
        <motion.button
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            onClick={onClick}
            className={`w-full h-11 rounded-md flex items-center justify-center gap-2 ${bgColor} ${textColor} text-sm font-bold shadow-sm hover:shadow-md transition-all duration-200 ${className}`}
        >
            {getIcon(icon)}
            <span>{label}</span>
        </motion.button>
    );
};

export default SocialButton;
