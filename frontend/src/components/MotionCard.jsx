import React from 'react';
import { motion } from 'framer-motion';

/**
 * MotionCard - Animated card wrapper with staggered entrance
 * Props:
 *   - children: Card content
 *   - delay: Animation delay in seconds
 *   - className: Additional CSS classes
 */
const MotionCard = ({ children, delay = 0, className = '' }) => {
    return (
        <motion.div
            className={`card card-custom ${className}`}
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
                duration: 0.5,
                delay: delay,
                ease: [0.25, 0.46, 0.45, 0.94], // easeOutQuad
            }}
            whileHover={{
                scale: 1.02,
                boxShadow: '0 8px 32px rgba(88, 166, 255, 0.15)',
                transition: { duration: 0.2 },
            }}
        >
            {children}
        </motion.div>
    );
};

export default MotionCard;
