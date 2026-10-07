<!-- impeccable:product-schema 1 -->

# Product Truth: ZZLUXORA

## Platform
desktop

## Stack
Python 3.10+, PySide6 / PyQt6 (Qt6 Universal Dual-Binding), NumPy, SoundFile, Librosa, Art-Net 4 DMX512 (UDP Socket)

## Users
- Primary: Lighting Directors (LD), Front-of-House (FOH) console operators, church worship technical teams, and audio-visual technicians.
- Secondary: Stage managers, audio engineers coordinating with lighting, and academic researchers in Music Information Retrieval (MIR).
- Usage context: Dim Front-of-House control booths, auditoriums during live praise & worship, multi-monitor setups, touchscreens and physical motorized fader surfaces.

## Product Purpose
Deliver an intelligent, autonomous, and uncompromised stage lighting control console that bridges computational Music Information Retrieval (STFT DSP -> Russell 2D Affective Plane -> Physical 4-Channel RGBW Decomposition) with deterministic high-rate Art-Net DMX512 transmission (43.07 FPS), while providing tactile grandMA3-grade live playback authority.

## Positioning
The only stage lighting console engineered specifically for praise & worship dynamics that combines real-time acoustic signal mood intelligence with industrial tour-grade console ergonomics (grandMA3 physical workflow and QLC+ luminaire utility), launching in under 500 ms with zero web-bloat or telemetry lock-in.

## Operating Context
- Physical environment: Low ambient light FOH booths, stage glare, high-pressure live service transitions where mistakes are immediately visible to hundreds of attendees.
- Technical environment: Linux Mint (ASUS VivoBook X407MA, 1366x768 compact screen) and Windows 11 (Acer Swift 3, 1920x1080 display) operating 100% offline via local Art-Net UDP 6454 (localhost SITL or SoftAP ESP32 transceiver).
- Rituals: Pre-service fixture patch validation, soundcheck audio analysis, playlist section cue auto-generation, and tactile live master playback execution via `[GO+]`.

## Capabilities and Constraints
- Hard real-time DMX refresh at 43.07 FPS (~23.22 ms packet interval) perfectly matching discrete DMX512-A wire transmission.
- Play-gated network security: UDP datagrams are strictly suppressed until the physical `[PLAY]` toggle is latched active.
- Non-blocking asynchronous audio processing: worker QThread ensures the UI never stutters, drops frames, or freezes during heavy FFT computation.
- Pure zero-GUI mathematical core: `core/` modules can run headless on micro-servers or CLI environments.

## Brand Commitments
- Voice & Tone: Industrial, authoritative, precision-engineered, uncompromising.
- Chrome & Aesthetics: Pure matte obsidian chassis, 10% purposeful luminescent accents, zero emojis, zero fake cyberpunk orbs/glows, zero decorative clutter.
- Interaction Law: Immediate tactile feedback; controls never jump or shift unexpectedly during live show execution.

## Evidence on Hand
- Verified 43.07 FPS transmission sync with DMX512 standard.
- 10 real benchmark worship tracks in `data/audio/` verified against STFT feature extraction.
- Validated hardware node: ESP32 DevKit V1 + MAX485 differential transceiver + 16x2 I2C LCD monitor.
- Verified fixture profiles: Alien AL36 (8CH RGB, 4 units at GIA Deliksari) and Kumastb STL47 (8CH RGBW, bench testing unit).

## Product Principles
1. **Safety First in the Booth**: A live console must never crash, freeze, or emit spurious packets. Blackout and stop actions take instantaneous priority over everything else.
2. **The Tool Disappears into the Performance**: Controls must be legible from 90 cm away in near-total darkness. Glanceability and muscle memory over novel decoration.
3. **No Slop, True Craftsmanship**: Every pixel, fader cap rib, and status indicator serves a measurable operational purpose.
4. **Deterministic Sub-16ms Feedback**: Fader adjustments and cue triggers must reflect instantaneously in visualizer telemetry and network buffers.

## Accessibility & Inclusion
- High-contrast Front-of-House readability: Minimum WCAG AAA contrast for all mission-critical telemetry and DMX channel statuses.
- Tabular figures (`tabular-nums`) across all numerical metrics to eliminate character jitter during live streaming.
- Full keyboard hotkey navigation (`Space` for Play/Stop, `Esc`/`B` for Blackout, `Ctrl+Z` for Undo, `Ctrl+O`/`Ctrl+S` for Project I/O).
