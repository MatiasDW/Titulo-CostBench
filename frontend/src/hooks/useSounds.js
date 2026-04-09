/**
 * useSounds – Professional financial platform sound effects.
 * 
 * Uses Web Audio API to synthesize tones — zero audio files.
 * Designed for a premium fintech experience: warm, deep, institutional.
 * 
 * Sound palette inspired by Bloomberg Terminal / professional trading desks:
 *   - Deep, warm tones (200-500 Hz base)
 *   - Sine + triangle waves (no harsh square)
 *   - Layered harmonics for richness
 *   - Very short duration (< 150ms) for responsiveness
 */
import { useCallback, useRef } from 'react';

// ── Shared AudioContext (lazy singleton) ──
let _ctx = null;
const getCtx = () => {
    if (!_ctx) _ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (_ctx.state === 'suspended') _ctx.resume();
    return _ctx;
};

/**
 * Play a professional tone with optional harmonics.
 */
const tone = (freq, dur = 0.08, type = 'sine', vol = 0.1, freq2 = null) => {
    try {
        const ctx = getCtx();
        const t = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, t);
        if (freq2) osc.frequency.exponentialRampToValueAtTime(freq2, t + dur);

        // Smooth envelope: quick attack, natural decay
        gain.gain.setValueAtTime(0, t);
        gain.gain.linearRampToValueAtTime(vol, t + 0.005);
        gain.gain.exponentialRampToValueAtTime(0.001, t + dur);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + dur);
    } catch { /* non-critical */ }
};

/**
 * Play a two-note chord for richer sound.
 */
const chord = (f1, f2, dur = 0.1, vol = 0.06) => {
    tone(f1, dur, 'sine', vol);
    tone(f2, dur, 'triangle', vol * 0.5);
};

const useSounds = () => {
    const last = useRef(0);
    const throttle = (fn, ms = 50) => (...args) => {
        const now = Date.now();
        if (now - last.current < ms) return;
        last.current = now;
        fn(...args);
    };

    // ── UI Interactions ──

    // Soft tactile click — subtle confirmation of any button press
    const playClick = useCallback(throttle(() => {
        tone(350, 0.04, 'sine', 0.06);
    }, 40), []);

    // Navigation tab switch — warm ascending fifth (C→G)
    const playNav = useCallback(throttle(() => {
        tone(262, 0.06, 'sine', 0.08);               // C4
        setTimeout(() => tone(392, 0.08, 'sine', 0.06), 50);  // G4
    }, 100), []);

    // Hover — barely audible tick
    const playHover = useCallback(throttle(() => {
        tone(440, 0.015, 'sine', 0.025);
    }, 120), []);

    // Toggle open/close — muted mechanical feel
    const playToggle = useCallback(throttle(() => {
        tone(330, 0.04, 'triangle', 0.06, 440);
    }, 80), []);

    // ── Actions & Feedback ──

    // Success — warm major chord (C-E-G), institutional bell
    const playSuccess = useCallback(throttle(() => {
        chord(262, 330, 0.1, 0.07);                    // C4 + E4
        setTimeout(() => chord(330, 392, 0.12, 0.06), 80);  // E4 + G4
        setTimeout(() => chord(392, 523, 0.15, 0.05), 160); // G4 + C5
    }, 250), []);

    // Error — low minor interval, brief
    const playError = useCallback(throttle(() => {
        tone(220, 0.08, 'triangle', 0.08);            // A3
        setTimeout(() => tone(208, 0.1, 'triangle', 0.06), 60); // ~Ab3
    }, 250), []);

    // Trade executed — satisfying "transactional" sound
    // Quick double-tap with ascending pitch, like a register confirmation
    const playTrade = useCallback(throttle(() => {
        tone(440, 0.03, 'sine', 0.08);                // A4 tick
        setTimeout(() => tone(554, 0.03, 'sine', 0.07), 35); // C#5
        setTimeout(() => chord(659, 880, 0.12, 0.06), 70);   // E5+A5 resolution
    }, 250), []);

    // ── Page / Feature sounds ──

    // Login success — warm welcome chord
    const playLogin = useCallback(throttle(() => {
        chord(330, 415, 0.08, 0.06);                    // E4+Ab4
        setTimeout(() => chord(440, 554, 0.1, 0.06), 70);  // A4+C#5
        setTimeout(() => chord(554, 659, 0.14, 0.05), 150); // C#5+E5
    }, 300), []);

    // Chat open — soft ascending notification
    const playChatOpen = useCallback(throttle(() => {
        tone(392, 0.05, 'sine', 0.05);                // G4
        setTimeout(() => tone(494, 0.06, 'sine', 0.05), 40); // B4
        setTimeout(() => tone(587, 0.07, 'sine', 0.04), 80); // D5
    }, 200), []);

    // Chat close — descending
    const playChatClose = useCallback(throttle(() => {
        tone(494, 0.04, 'sine', 0.04);
        setTimeout(() => tone(392, 0.05, 'sine', 0.04), 35);
    }, 200), []);

    // Message sent — quick whoosh-like
    const playSend = useCallback(throttle(() => {
        tone(400, 0.04, 'triangle', 0.05, 600);
    }, 150), []);

    // Message received — gentle notification ping
    const playReceive = useCallback(throttle(() => {
        chord(523, 659, 0.08, 0.04);                  // C5+E5
    }, 150), []);

    // Card/item select — toggle with a warm pop
    const playSelect = useCallback(throttle(() => {
        tone(440, 0.035, 'sine', 0.07);
        setTimeout(() => tone(554, 0.04, 'sine', 0.05), 30);
    }, 60), []);

    // Card/item deselect — descending pop
    const playDeselect = useCallback(throttle(() => {
        tone(494, 0.035, 'sine', 0.05);
        setTimeout(() => tone(392, 0.04, 'sine', 0.04), 30);
    }, 60), []);

    // Save / confirm — solid confirmation
    const playSave = useCallback(throttle(() => {
        chord(349, 440, 0.07, 0.06);                    // F4+A4
        setTimeout(() => chord(440, 554, 0.1, 0.06), 60);  // A4+C#5
        setTimeout(() => chord(523, 659, 0.14, 0.05), 130); // C5+E5
    }, 300), []);

    // Refresh / update data
    const playRefresh = useCallback(throttle(() => {
        tone(350, 0.04, 'triangle', 0.05, 500);
        setTimeout(() => tone(500, 0.05, 'triangle', 0.04, 700), 50);
    }, 200), []);

    return {
        // UI basics
        playClick,
        playNav,
        playHover,
        playToggle,
        // Feedback
        playSuccess,
        playError,
        playTrade,
        // Features
        playLogin,
        playChatOpen,
        playChatClose,
        playSend,
        playReceive,
        playSelect,
        playDeselect,
        playSave,
        playRefresh,
    };
};

export default useSounds;
