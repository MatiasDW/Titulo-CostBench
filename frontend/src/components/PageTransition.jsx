/**
 * PageTransition – Smooth animated wrapper for page content.
 * Wrap any route content in this for a fade + slide entrance.
 */
import React from 'react';
import { motion } from 'framer-motion';

const variants = {
    initial: {
        opacity: 0,
        y: 12,
        scale: 0.995,
    },
    animate: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: {
            duration: 0.3,
            ease: [0.25, 0.46, 0.45, 0.94], // easeOutQuad
        },
    },
    exit: {
        opacity: 0,
        y: -8,
        scale: 0.995,
        transition: {
            duration: 0.15,
            ease: 'easeIn',
        },
    },
};

const PageTransition = ({ children, pageKey }) => (
    <motion.div
        key={pageKey}
        variants={variants}
        initial="initial"
        animate="animate"
        exit="exit"
        style={{ width: '100%', minHeight: '100%' }}
    >
        {children}
    </motion.div>
);

export default PageTransition;
