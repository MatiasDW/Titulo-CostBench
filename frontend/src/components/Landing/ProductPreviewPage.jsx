import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    FaArrowRight,
    FaBuilding,
    FaChartLine,
    FaCheckCircle,
    FaClipboardCheck,
    FaGlobeAmericas,
    FaHome,
    FaSearchDollar,
    FaUserTie,
} from 'react-icons/fa';
import AnimatedBackground from '../AnimatedBackground';
import SignUpModal from '../Auth/SignUpModal';
import './ProductPreviewPage.css';

const PREVIEW_BLOCKS = [
    {
        title: 'Scloda Real Estate Advisory',
        text: 'Asset screening, legal checkpoints, expected total acquisition cost, and execution risk review.',
        icon: <FaBuilding size={16} />,
    },
    {
        title: 'Scloda Trade Context',
        text: 'Macro interpretation for UF, FX, and rate cycle effects before buying into Chilean assets.',
        icon: <FaChartLine size={16} />,
    },
    {
        title: 'Execution Pipeline',
        text: 'A step-by-step path from first objective to close, including ownership, status, and evidence.',
        icon: <FaClipboardCheck size={16} />,
    },
];

const PREVIEW_TIMELINE = [
    'Investor profile completed',
    'Market + area shortlist generated',
    'Risk and cost model validated',
    'Closing readiness checklist prepared',
];

const ProductPreviewPage = () => {
    const [showSignUp, setShowSignUp] = useState(false);

    return (
        <div className="preview-page">
            <AnimatedBackground />

            <header className="preview-nav">
                <img src="/img/costbench_logo.svg" alt="CostBench" />
                <div className="preview-nav-actions">
                    <Link to="/landing" className="preview-link">
                        Back to landing
                    </Link>
                    <button onClick={() => setShowSignUp(true)} className="preview-signup">
                        Create account
                    </button>
                </div>
            </header>

            <main className="preview-main">
                <motion.section
                    className="preview-hero"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.45 }}
                >
                    <span className="preview-kicker">
                        <FaGlobeAmericas size={12} /> Product preview
                    </span>
                    <h1>Explore CostBench before creating an account.</h1>
                    <p>
                        This public preview shows the product logic and where Scloda creates value for foreign
                        investors in Chilean real estate.
                    </p>
                    <button className="preview-cta" onClick={() => setShowSignUp(true)}>
                        Unlock full access <FaArrowRight size={13} />
                    </button>
                </motion.section>

                <section className="preview-grid">
                    {PREVIEW_BLOCKS.map((block, index) => (
                        <motion.article
                            className="preview-card"
                            key={block.title}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, amount: 0.2 }}
                            transition={{ duration: 0.4, delay: index * 0.08 }}
                        >
                            <div className="preview-card-icon">{block.icon}</div>
                            <h2>{block.title}</h2>
                            <p>{block.text}</p>
                        </motion.article>
                    ))}
                </section>

                <section className="preview-advisor">
                    <div className="preview-advisor-head">
                        <span className="preview-advisor-avatar">
                            <FaUserTie size={16} />
                        </span>
                        <strong>Scloda insight example</strong>
                    </div>
                    <p>
                        “For this profile, Santiago multifamily appears attractive, but the FX/UF scenario raises
                        financing sensitivity. My recommendation: prioritize lower leverage and lock legal due diligence
                        before offer.”
                    </p>
                    <div className="preview-advisor-tags">
                        <span>
                            <FaSearchDollar size={11} /> Cost-risk balance
                        </span>
                        <span>
                            <FaHome size={11} /> Real estate fit
                        </span>
                        <span>
                            <FaCheckCircle size={11} /> Actionable next step
                        </span>
                    </div>
                </section>

                <section className="preview-timeline">
                    <h3>Execution flow snapshot</h3>
                    <ul>
                        {PREVIEW_TIMELINE.map((item) => (
                            <li key={item}>
                                <FaCheckCircle size={12} /> {item}
                            </li>
                        ))}
                    </ul>
                </section>
            </main>

            <SignUpModal isOpen={showSignUp} onClose={() => setShowSignUp(false)} />
        </div>
    );
};

export default ProductPreviewPage;
