document.addEventListener('DOMContentLoaded', () => {
    // Web Audio API Context
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    let audioCtx = new AudioContext();

    // Buffers
    let hoverBuffer = null;
    let enterBuffer = null;

    // Loader function
    const loadSound = async (url) => {
        try {
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            return await audioCtx.decodeAudioData(arrayBuffer);
        } catch (error) {
            console.error('Error loading sound:', url, error);
            return null;
        }
    };

    // Load sounds
    loadSound('audio/hover.mp3').then(buf => hoverBuffer = buf);
    loadSound('audio/enter.mp3').then(buf => enterBuffer = buf);

    // Play function with volume
    const playSound = (buffer, volume) => {
        if (!buffer || !audioCtx) return;

        // Create source and gain node
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        const gainNode = audioCtx.createGain();

        // Set volume
        gainNode.gain.value = volume;

        // Connect: Source -> Gain -> Destination
        source.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        // Play
        source.start(0);
    };

    const welcomeScreen = document.getElementById('welcome-screen');
    let audioUnlocked = false;

    // Function to unlock audio and enter site
    const enterSite = () => {
        // Resume AudioContext on user interaction (critical for mobile)
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }

        if (!audioUnlocked) {
            // Play enter sound with strict volume control
            // Volume 0.02 for enter sound
            if (enterBuffer) {
                playSound(enterBuffer, 0.02);
            }
            audioUnlocked = true;
        }

        // Animation to fade out welcome screen
        welcomeScreen.classList.add('opacity-0', 'pointer-events-none');

        setTimeout(() => {
            welcomeScreen.remove();
        }, 1000);
    };

    // Add click listener to welcome screen
    if (welcomeScreen) {
        welcomeScreen.addEventListener('click', enterSite);
    }

    // Select all menu items for hover effect and mobile interaction
    const menuItems = document.querySelectorAll('main a');

    menuItems.forEach(item => {
        // Mouse Enter (Desktop Hover)
        item.addEventListener('mouseenter', () => {
            if (audioUnlocked && hoverBuffer) {
                // Volume 0.1 for hover
                playSound(hoverBuffer, 0.1);
            }
        });

        // Click Handler (Mobile Tap Logic)
        item.addEventListener('click', (e) => {
            // Check if device is mobile (width < 768px matches Tailwind 'md')
            const isMobile = window.innerWidth < 768;

            if (isMobile) {
                if (item.classList.contains('mobile-active')) {
                    // Second tap: already active, allow navigation (do nothing here)
                    return;
                } else {
                    // First tap: prevent navigation, activate state
                    e.preventDefault();

                    // Deactivate others
                    menuItems.forEach(other => other.classList.remove('mobile-active'));

                    // Activate this one
                    item.classList.add('mobile-active');

                    // Play hover sound
                    if (audioUnlocked && hoverBuffer) {
                        playSound(hoverBuffer, 0.1);
                    }
                }
            }
        });
    });

    // Optional: Click outside to deselect on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth < 768 && !e.target.closest('main a')) {
            menuItems.forEach(item => item.classList.remove('mobile-active'));
        }
    });
});
