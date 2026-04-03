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
import chileAraucariaVolcano from '../../assets/landing/chile-araucaria-volcano.jpg';
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

const CHILE_MAP_POINTS = [
    { city: 'Arica y Parinacota', capital: 'Arica', focus: 'Border commerce and logistics gateway.', x: 106.7, y: 23.0 },
    { city: 'Tarapaca', capital: 'Iquique', focus: 'Free-zone momentum and port-linked activity.', x: 109.6, y: 52.1 },
    { city: 'Antofagasta', capital: 'Antofagasta', focus: 'Mining services with executive rental demand.', x: 105.2, y: 109.1 },
    { city: 'Atacama', capital: 'Copiapo', focus: 'Energy corridors and strategic land optionality.', x: 106.4, y: 171.0 },
    { city: 'Coquimbo', capital: 'La Serena', focus: 'Coastal second-home demand and tourism flow.', x: 91.1, y: 213.1 },
    { city: 'Valparaiso', capital: 'Valparaiso', focus: 'Short-stay coastal cash flow and liquidity.', x: 84.9, y: 265.6 },
    { city: 'Metropolitana', capital: 'Santiago', focus: 'Highest liquidity and absorption depth.', x: 100.7, y: 272.2 },
    { city: "O'Higgins", capital: 'Rancagua', focus: 'Industrial spillover and suburban growth.', x: 99.6, y: 284.2 },
    { city: 'Maule', capital: 'Talca', focus: 'Affordable entry points with agro logistics.', x: 84.3, y: 305.2 },
    { city: 'Nuble', capital: 'Chillan', focus: 'Regional densification near major routes.', x: 76.9, y: 324.8 },
    { city: 'Biobio', capital: 'Concepcion', focus: 'University and industrial rental profile.', x: 61.1, y: 328.5 },
    { city: 'La Araucania', capital: 'Temuco', focus: 'Lifestyle migration and land thesis.', x: 68.8, y: 360.3 },
    { city: 'Los Rios', capital: 'Valdivia', focus: 'Amenity-driven housing demand.', x: 57.9, y: 378.3 },
    { city: 'Los Lagos', capital: 'Puerto Montt', focus: 'Lake district premium valuation.', x: 62.9, y: 405.8 },
    { city: 'Aysen', capital: 'Coyhaique', focus: 'Frontier positioning with low density upside.', x: 77.4, y: 474.0 },
    { city: 'Magallanes', capital: 'Punta Arenas', focus: 'Long-horizon strategic land play.', x: 96.7, y: 600.4 },
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
    const [hoveredRegion, setHoveredRegion] = useState(null);
    const activeRegion = hoveredRegion || CHILE_MAP_POINTS[6];

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

                    <div className="landing-hero-side">
                        <motion.article className="landing-map-card" variants={fadeCard} initial="hidden" animate="show">
                            <div className="landing-map-head">
                                <strong>Chile Regions Monitor</strong>
                                <span>16 regions tracked</span>
                            </div>
                            <div className="landing-map-body">
                                <div className="landing-map-stage">
                                    <svg className="chile-map-svg" viewBox="0 0 180 620" aria-hidden="true">
                                        <path
                                            className="chile-map-outline"
                                            d="M141.53 73.17 L148.05 96.13 L160.07 93.85 L162.09 98.02 L156.37 115.31 L138.24 123.53 L138.76 151.27 L135.29 156.63 L140.27 163.17 L128.52 173.52 L117.62 189.14 L111.67 204.27 L113.24 220.39 L102.98 237.52 L110.65 266.26 L114.98 269.3 L114.93 284.61 L105.43 300.87 L105.82 314.78 L93.21 325.65 L93.27 340.95 L98.33 357.2 L88.36 363.24 L83.91 378.1 L79.99 395.15 L82.81 415.45 L76.11 418.83 L80 438.04 L87.52 444.35 L82.03 451.34 L89.75 454.68 L91.53 460.95 L84.26 464.1 L86.05 473.88 L79.97 495.92 L71.14 510.14 L73.08 518.56 L67.8 529.12 L55.02 536.44 L56.48 554.1 L62.35 560.14 L73.43 559.06 L73.11 571.53 L80.01 581.24 L120.24 583.47 L135.68 586.08 L120.86 585.95 L112.84 590.05 L97.82 596.06 L95.14 611.61 L88.09 612 L69.3 606.59 L50.24 594.99 L29.53 585.47 L24.31 574.92 L29.03 565.16 L20.65 554.09 L18.52 525.71 L25.6 509.69 L43.18 496.83 L17.91 491.97 L33.77 477.26 L39.44 449.61 L57.94 455.47 L66.64 420.97 L55.47 416.55 L50.26 437.33 L39.77 434.99 L44.99 411.17 L50.67 380.33 L58.32 368.95 L53.52 352.7 L52.15 333.94 L59.17 333.4 L69.38 306.51 L80.89 279.88 L87.94 255.07 L84.11 230.12 L89.08 216.38 L87.08 195.83 L96.82 175.5 L99.82 143.3 L105.17 108.72 L110.37 71.49 L109.15 44.24 L105.69 20.79 L114.25 16.54 L118.71 8 L126.87 19.32 L129.09 31.34 L137.83 38.39 L132.58 54.5 L141.53 73.17 Z"
                                        />
                                        {CHILE_MAP_POINTS.map((region) => (
                                            <g
                                                key={region.city}
                                                className={`chile-map-pin ${activeRegion.city === region.city ? 'active' : ''}`}
                                                transform={`translate(${region.x} ${region.y})`}
                                                onMouseEnter={() => setHoveredRegion(region)}
                                                onMouseLeave={() => setHoveredRegion(null)}
                                                onFocus={() => setHoveredRegion(region)}
                                                onBlur={() => setHoveredRegion(null)}
                                                onKeyDown={(event) => {
                                                    if (event.key === 'Enter' || event.key === ' ') {
                                                        event.preventDefault();
                                                        setHoveredRegion(region);
                                                    }
                                                }}
                                                tabIndex={0}
                                                role="button"
                                                aria-label={region.city}
                                            >
                                                <circle className="chile-map-pin-ring" r="6.4" />
                                                <circle className="chile-map-pin-core" r="3.2" />
                                            </g>
                                        ))}
                                    </svg>
                                </div>
                                <article className="control-room-region-advice">
                                    <span className="region-active-label">Region active</span>
                                    <h4>{activeRegion.city}</h4>
                                    <p className="region-capital">{activeRegion.capital}</p>
                                    <p>{activeRegion.focus}</p>
                                    <small>Hover regions to explore local signals.</small>
                                </article>
                            </div>
                        </motion.article>

                        <motion.aside className="landing-control-room" variants={stagger} initial="hidden" animate="show">
                            <div className="control-room-main">
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
                                <article className="control-room-photo-card">
                                    <img src={chileAraucariaVolcano} alt="Chilean biodiversity landscape" loading="lazy" />
                                    <div className="control-room-photo-overlay">
                                        <h4>Flora & fauna signal</h4>
                                        <p>Context layer for long-horizon desirability in Chile.</p>
                                    </div>
                                </article>
                            </div>
                        </motion.aside>
                    </div>
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
