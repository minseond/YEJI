import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface PageContainerProps {
    children: ReactNode;
    className?: string; // Allow custom classes
}

const PageContainer = ({ children, className = "" }: PageContainerProps) => {
    return (
        <motion.div
            className={`w-full max-w-4xl mx-auto pt-24 pb-24 px-6 flex flex-col items-center min-h-screen text-white/90 ${className}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
        >
            {children}
        </motion.div>
    );
};

export default PageContainer;
