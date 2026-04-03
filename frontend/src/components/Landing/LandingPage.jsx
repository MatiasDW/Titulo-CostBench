import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import Flag from 'react-world-flags';
import {
    FaArrowRight,
    FaBalanceScale,
    FaBuilding,
    FaChartLine,
    FaCheckCircle,
    FaCompass,
    FaEnvelopeOpenText,
    FaFileContract,
    FaGlobeAmericas,
    FaHandshake,
    FaHome,
    FaMapMarkedAlt,
    FaMoneyBillWave,
    FaPassport,
    FaPlayCircle,
    FaSearchDollar,
    FaShieldAlt,
    FaSlidersH,
    FaUserCheck,
    FaUserTie,
} from 'react-icons/fa';
import AnimatedBackground from '../AnimatedBackground';
import SignUpModal from '../Auth/SignUpModal';
import chileSantiagoSkyline from '../../assets/landing/chile-santiago-skyline.jpg';
import chileValparaisoHills from '../../assets/landing/chile-valparaiso-hills.jpg';
import chilePatagoniaLake from '../../assets/landing/chile-patagonia-lake.jpg';
import chilePuertoVaras from '../../assets/landing/chile-puerto-varas.jpg';
import chileLasCondesSanhattan from '../../assets/landing/chile-las-condes-sanhattan.jpg';
import santiagoNight from '../../assets/santiago_night.png';
import './LandingPage.css';

const TRUST_BADGES = [
    'Structured flow for non-residents',
    'Institutional-grade due diligence',
    'Hybrid model: subscription + commission',
];

const HERO_STATS = [
    { label: 'Legal checklist', value: '42', meta: 'acquisition milestones' },
    { label: 'Macro feeds', value: '7', meta: 'critical data sources' },
    { label: 'Scloda modules', value: '2', meta: 'Real Estate + Trade' },
];

const PROBLEM_POINTS = [
    {
        title: 'Buying remotely is operationally hard',
        text: 'Legal language, local procedures, and closing coordination become painful without an in-country system.',
        icon: <FaPassport size={18} />,
    },
    {
        title: 'Total cost is often hidden',
        text: 'Listing price is not enough: taxes, legal fees, and execution risk materially affect return.',
        icon: <FaSearchDollar size={18} />,
    },
    {
        title: 'Decision data lives in silos',
        text: 'UF, FX, macro shifts, and property opportunities are fragmented across disconnected tools.',
        icon: <FaChartLine size={18} />,
    },
];

const SOLUTION_STEPS = [
    {
        title: 'Investor diagnosis',
        text: 'We define profile, target return, ticket size, and constraints before any property search.',
        icon: <FaCompass size={18} />,
    },
    {
        title: 'Filtering and due diligence',
        text: 'We prioritize assets and surface critical legal/financial risks before capital is committed.',
        icon: <FaBalanceScale size={18} />,
    },
    {
        title: 'Traceable execution',
        text: 'From first screen to final closing, every step is visible with owner, status, and evidence.',
        icon: <FaHandshake size={18} />,
    },
];

const PRODUCT_MODULES = [
    {
        title: 'Scloda Real Estate',
        text: 'Guided education and decision support for international buyers entering Chile.',
        tag: 'Subscription',
        icon: <FaBuilding size={16} />,
    },
    {
        title: 'Scloda Trade',
        text: 'Macro context layer to read cycle timing, volatility, and exposure before buying.',
        tag: 'Subscription',
        icon: <FaSlidersH size={16} />,
    },
    {
        title: 'Transaction layer',
        text: 'Acquire land or property through platform workflows and monetize with closing commissions.',
        tag: 'Commission',
        icon: <FaMoneyBillWave size={16} />,
    },
];

const COMPLIANCE_POINTS = [
    {
        title: 'Compliance path by design',
        text: 'The workflow is structured to coexist with KYC, AML controls, and operational governance.',
        icon: <FaShieldAlt size={16} />,
    },
    {
        title: 'Document governance',
        text: 'Checklists and evidence trails reduce execution mistakes in high-stakes transactions.',
        icon: <FaFileContract size={16} />,
    },
    {
        title: 'Local execution bridge',
        text: 'A structured handoff between foreign investor, local advisors, and closing operations.',
        icon: <FaUserCheck size={16} />,
    },
];

const REAL_ESTATE_MARQUEE = [
    'Santiago Residential',
    'Valparaiso Coastal Assets',
    'Concepcion Expansion Zones',
    'Land Lots',
    'Multifamily',
    'Commercial Units',
    'UF-Adjusted Planning',
];

const SCLODA_CAPABILITIES = [
    'Reads macro + market context to explain timing in plain English',
    'Understands Chile-specific factors (UF, FX, cost of debt, local cycle)',
    'Connects real estate opportunities with risk, return, and execution tradeoffs',
];

const CHILE_REAL_ESTATE_SPOTS = [
    {
        title: 'Santiago Financial District',
        subtitle: 'High-liquidity apartments and executive demand',
        image: chileSantiagoSkyline,
    },
    {
        title: 'Valparaiso Hills',
        subtitle: 'Tourism-oriented rentals with strong visual identity',
        image: chileValparaisoHills,
    },
    {
        title: 'Puerto Varas Lake District',
        subtitle: 'Premium second-home and relocation market',
        image: chilePuertoVaras,
    },
    {
        title: 'Patagonia Lifestyle Assets',
        subtitle: 'Long-horizon land and nature-driven developments',
        image: chilePatagoniaLake,
    },
    {
        title: 'Las Condes / Sanhattan',
        subtitle: 'Prime office-residential zone with strong corporate demand',
        image: chileLasCondesSanhattan,
    },
    {
        title: 'Santiago Night Market View',
        subtitle: 'Urban density, transport access, and rental absorption',
        image: santiagoNight,
    },
];

const container = {
    hidden: { opacity: 0, y: 22 },
    show: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
    },
};

const stagger = {
    hidden: {},
    show: {
        transition: {
            staggerChildren: 0.08,
            delayChildren: 0.12,
        },
    },
};

const fadeCard = {
    hidden: { opacity: 0, y: 14 },
    show: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] },
    },
};

const shimmerMotion = {
    animate: {
        backgroundPositionX: ['0%', '100%'],
    },
    transition: {
        duration: 2.8,
        repeat: Infinity,
        ease: 'linear',
    },
};

const LandingPage = () => {
    const [showSignUp, setShowSignUp] = useState(false);

    return (
        <div className="landing-page">
            <AnimatedBackground />
            <div className="landing-fog" />
            <div className="landing-fog second" />

            <header className="landing-nav">
                <div className="landing-brand">
                    <img src="/img/costbench_logo.svg" alt="CostBench" />
                </div>
                <nav className="landing-anchor-nav">
                    <a href="#scloda">Scloda</a>
                    <a href="#locations">Places</a>
                    <a href="#problem">Problem</a>
                    <a href="#solution">Solution</a>
                    <a href="#model">Model</a>
                </nav>
                <div className="landing-nav-actions">
                    <span className="landing-flag-chip">
                        <Flag code="CL" height="13" /> Chile-first
                    </span>
                    <Link className="landing-login" to="/login">
                        Log in
                    </Link>
                    <button className="landing-signup" onClick={() => setShowSignUp(true)}>
                        Create account
                    </button>
                </div>
            </header>

            <main className="landing-main">
                <motion.section className="landing-hero" variants={container} initial="hidden" animate="show">
                    <div className="landing-hero-copy">
                        <span className="landing-kicker">
                            <Flag code="CL" height="12" /> Cross-border real estate intelligence
                        </span>
                        <div className="landing-scloda-inline">
                            <span className="landing-scloda-inline-icon">
                                <FaUserTie size={14} />
                            </span>
                            <span>Scloda is your AI advisor for Chile real estate + market intelligence</span>
                        </div>
                        <h1>Invest in Chile as a foreign buyer with a professional end-to-end system.</h1>
                        <p>
                            CostBench combines education, macro intelligence, and real estate execution so complex
                            cross-border decisions become controlled, transparent, and investment-ready.
                        </p>
                        <div className="landing-hero-actions">
                            <button className="landing-cta-primary" onClick={() => setShowSignUp(true)}>
                                Start onboarding <FaArrowRight size={13} />
                            </button>
                            <Link className="landing-cta-secondary" to="/login">
                                I already have an account
                            </Link>
                            <Link className="landing-cta-ghost-link" to="/preview">
                                <span className="landing-cta-ghost" role="button">
                                    <FaPlayCircle size={14} /> See how it works
                                </span>
                            </Link>
                        </div>
                        <div className="landing-trust-row">
                            {TRUST_BADGES.map((badge) => (
                                <span key={badge}>
                                    <FaCheckCircle size={12} /> {badge}
                                </span>
                            ))}
                        </div>
                    </div>

                    <motion.aside className="landing-control-room" variants={stagger} initial="hidden" animate="show">
                        <div className="control-room-header">
                            <span>Control Room</span>
                            <motion.span className="control-room-pill" {...shimmerMotion}>
                                Live Strategy
                            </motion.span>
                        </div>
                        <div className="control-room-grid">
                            {HERO_STATS.map((stat) => (
                                <motion.article
                                    className="control-room-card"
                                    key={stat.label}
                                    variants={fadeCard}
                                    whileHover={{ y: -4, scale: 1.02, rotateX: 6 }}
                                    transition={{ type: 'spring', stiffness: 280, damping: 20 }}
                                >
                                    <small>{stat.label}</small>
                                    <strong>{stat.value}</strong>
                                    <span>{stat.meta}</span>
                                </motion.article>
                            ))}
                        </div>
                        <motion.div className="control-room-line" variants={fadeCard}>
                            <div />
                        </motion.div>
                        <motion.ul className="control-room-checks" variants={fadeCard}>
                            <li>
                                <FaHome size={12} /> Prioritized real estate pipeline
                            </li>
                            <li>
                                <FaGlobeAmericas size={12} /> Structured non-resident flow
                            </li>
                            <li>
                                <FaMapMarkedAlt size={12} /> Macro + land signal alignment
                            </li>
                        </motion.ul>
                    </motion.aside>
                </motion.section>

                <motion.section
                    id="market"
                    className="landing-section marquee-wrap"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.3 }}
                >
                    <div className="landing-marquee">
                        <div className="landing-marquee-track">
                            {[...REAL_ESTATE_MARQUEE, ...REAL_ESTATE_MARQUEE].map((item, idx) => (
                                <span key={`${item}-${idx}`}>
                                    <FaBuilding size={12} /> {item}
                                </span>
                            ))}
                        </div>
                    </div>
                </motion.section>

                <motion.section
                    id="scloda"
                    className="landing-section scloda-section"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <div className="scloda-spotlight">
                        <motion.div
                            className="scloda-avatar"
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                        >
                            <FaUserTie size={32} />
                        </motion.div>
                        <div className="scloda-copy">
                            <span className="scloda-label">Powered by Scloda</span>
                            <h2>Scloda is the core paid value of the product.</h2>
                            <p>
                                The premium layer is not just access to screens. It is expert-grade advisory from
                                an AI agent trained to reason about Chilean market behavior and real estate
                                execution decisions.
                            </p>
                            <ul className="scloda-list">
                                {SCLODA_CAPABILITIES.map((item) => (
                                    <li key={item}>
                                        <FaCheckCircle size={12} /> {item}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </motion.section>

                <motion.section
                    id="locations"
                    className="landing-section"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <h2>Chile locations with strong real estate appeal</h2>
                    <p className="landing-section-intro">
                        We prioritize markets where foreign investors can combine quality-of-life demand,
                        rental depth, and long-term pricing resilience.
                    </p>
                    <div className="landing-photo-grid">
                        {CHILE_REAL_ESTATE_SPOTS.map((spot, index) => (
                            <motion.article
                                className="landing-photo-card"
                                key={spot.title}
                                initial={{ opacity: 0, y: 16 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, amount: 0.25 }}
                                transition={{ duration: 0.45, delay: index * 0.07 }}
                                whileHover={{ y: -6, scale: 1.01 }}
                            >
                                <img src={spot.image} alt={spot.title} loading="lazy" />
                                <div className="landing-photo-overlay">
                                    <h3>{spot.title}</h3>
                                    <p>{spot.subtitle}</p>
                                </div>
                            </motion.article>
                        ))}
                    </div>
                    <p className="landing-photo-credit">
                        Real photography source: Pexels (used for visual context in this prototype).
                    </p>
                </motion.section>

                <motion.section
                    id="problem"
                    className="landing-section"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <h2>The actual problem for foreign investors</h2>
                    <motion.div className="landing-grid three" variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.2 }}>
                        {PROBLEM_POINTS.map((item) => (
                            <motion.article
                                key={item.title}
                                className="landing-card issue"
                                variants={fadeCard}
                                whileHover={{ y: -6, scale: 1.01 }}
                                transition={{ type: 'spring', stiffness: 240, damping: 19 }}
                            >
                                <div className="landing-card-icon">{item.icon}</div>
                                <h3>{item.title}</h3>
                                <p>{item.text}</p>
                            </motion.article>
                        ))}
                    </motion.div>
                </motion.section>

                <motion.section
                    id="solution"
                    className="landing-section dual"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <div>
                        <h2>How we solve it in practice</h2>
                        <p className="landing-section-intro">
                            We do not start with random features. We start with execution friction and build a
                            sequence that gets you to a lower-risk closing.
                        </p>
                        <div className="landing-steps">
                            {SOLUTION_STEPS.map((step, idx) => (
                                <div className="landing-step" key={step.title}>
                                    <span className="landing-step-index">0{idx + 1}</span>
                                    <div>
                                        <h3>{step.title}</h3>
                                        <p>{step.text}</p>
                                    </div>
                                    <span className="landing-step-icon">{step.icon}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="landing-side-stack">
                        <article className="landing-side-card">
                            <h3>Value stack</h3>
                            <ul>
                                <li>Guided education by Scloda</li>
                                <li>Total-cost and risk intelligence</li>
                                <li>Stage-by-stage status monitoring</li>
                                <li>Transaction-ready closing preparation</li>
                            </ul>
                        </article>
                        <article className="landing-side-card accent">
                            <h3>Commercial objective</h3>
                            <p>
                                Build an institutional-grade international investing experience that captures value on
                                subscriptions and successful closings.
                            </p>
                        </article>
                    </div>
                </motion.section>

                <motion.section
                    id="model"
                    className="landing-section"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <h2>Modules and monetization engine</h2>
                    <div className="landing-grid three">
                        {PRODUCT_MODULES.map((module) => (
                            <motion.article
                                className="landing-card soft module"
                                key={module.title}
                                whileHover={{ y: -6, scale: 1.01 }}
                                transition={{ type: 'spring', stiffness: 240, damping: 18 }}
                            >
                                <div className="landing-module-head">
                                    <span className="module-icon">{module.icon}</span>
                                    <span className="module-tag">{module.tag}</span>
                                </div>
                                <h3>{module.title}</h3>
                                <p>{module.text}</p>
                            </motion.article>
                        ))}
                    </div>
                </motion.section>

                <motion.section
                    className="landing-section"
                    variants={container}
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <div className="landing-business-model">
                        <h2>Trust framework and professional standard</h2>
                        <p>
                            The product is designed to capture commercial upside without improvising on execution or
                            operational control.
                        </p>
                        <div className="landing-grid three compliance-grid">
                            {COMPLIANCE_POINTS.map((point) => (
                                <article key={point.title} className="landing-compliance-card">
                                    <span className="landing-compliance-icon">{point.icon}</span>
                                    <h3>{point.title}</h3>
                                    <p>{point.text}</p>
                                </article>
                            ))}
                        </div>
                        <div className="landing-final-actions">
                            <button className="landing-cta-primary" onClick={() => setShowSignUp(true)}>
                                Create account now
                            </button>
                            <Link className="landing-login inline" to="/login">
                                Go to login
                            </Link>
                            <span className="landing-mail-hint">
                                <FaEnvelopeOpenText size={12} /> onboarding in under 5 minutes
                            </span>
                        </div>
                    </div>
                </motion.section>
            </main>

            <SignUpModal isOpen={showSignUp} onClose={() => setShowSignUp(false)} />
        </div>
    );
};

export default LandingPage;
