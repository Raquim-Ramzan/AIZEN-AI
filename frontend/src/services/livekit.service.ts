import { Room, RoomEvent, RemoteParticipant, LocalParticipant, RemoteTrack, RemoteTrackPublication, Track, TrackEvent } from 'livekit-client';
import { API_CONFIG } from '@/config/api.config';

// Voice state events for UI synchronization
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VoiceStateEvent {
    state: VoiceState;
    timestamp: number;
    metadata?: {
        audioLevel?: number;
        duration?: number;
        error?: string;
    };
}

export interface TTSConfig {
    voice: string;
    speed?: number;
    pitch?: number;
}

export interface LiveKitConfig {
    url: string;
    token?: string;
    roomName?: string;
}

type VoiceStateHandler = (event: VoiceStateEvent) => void;
type AudioDataHandler = (audioData: Float32Array) => void;

// Default LiveKit configuration (URL is fetched from backend)
const DEFAULT_LIVEKIT_CONFIG: LiveKitConfig = {
    url: '',  // Will be set from backend token response
    roomName: 'aizen-voice'
};

/**
 * LiveKit Voice Service
 * Manages real-time audio streaming, VAD, and TTS playback
 */
export class LiveKitVoiceService {
    private room: Room | null = null;
    private audioContext: AudioContext | null = null;
    private mediaStream: MediaStream | null = null;
    private analyser: AnalyserNode | null = null;
    private vadProcessor: ScriptProcessorNode | null = null;

    private isListening: boolean = false;
    private isSpeaking: boolean = false;
    private currentState: VoiceState = 'idle';
    private isConnected: boolean = false;

    // LiveKit connection
    private livekitConfig: LiveKitConfig = DEFAULT_LIVEKIT_CONFIG;

    // VAD Configuration
    private vadThreshold: number = 0.02;  // Voice activity threshold
    private vadSilenceTimeout: number = 1500;  // ms of silence before stopping
    private silenceTimer: NodeJS.Timeout | null = null;

    // Event handlers
    private stateHandlers: VoiceStateHandler[] = [];
    private audioHandlers: AudioDataHandler[] = [];

    // TTS Configuration (Charon voice profile)
    private ttsConfig: TTSConfig = {
        voice: 'charon',
        speed: 1.0,
        pitch: 1.0
    };

    // Auto-speak toggle
    private autoSpeak: boolean = true;

    constructor() {
        // Initialize on first user interaction (required for AudioContext)
    }

    /**
     * Set LiveKit connection configuration
     */
    setLiveKitConfig(config: Partial<LiveKitConfig>): void {
        this.livekitConfig = { ...this.livekitConfig, ...config };
    }

    /**
     * Set auto-speak toggle
     */
    setAutoSpeak(enabled: boolean): void {
        this.autoSpeak = enabled;
        console.log(`[LiveKit] Auto-speak: ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Get auto-speak status
     */
    getAutoSpeak(): boolean {
        return this.autoSpeak;
    }

    /**
     * Connect to LiveKit room (for full duplex audio)
     */
    async connectToRoom(token: string): Promise<boolean> {
        try {
            console.log(`[LiveKit] Connecting to room at ${this.livekitConfig.url}...`);

            if (this.room) {
                await this.room.disconnect();
            }

            this.room = new Room({
                adaptiveStream: true,
                dynacast: true,
            });

            // Setup room event listeners
            this.room
                .on(RoomEvent.Connected, () => {
                    this.isConnected = true;
                    this.emitState('idle');
                    console.log('[LiveKit] Connected to room');
                })
                .on(RoomEvent.Disconnected, () => {
                    this.isConnected = false;
                    this.emitState('idle');
                    console.log('[LiveKit] Disconnected from room');
                })
                .on(RoomEvent.TrackSubscribed, (track: RemoteTrack) => {
                    if (track.kind === Track.Kind.Audio) {
                        console.log('[LiveKit] Subscribed to audio track');
                        // Attach audio track to play it
                        const audioElement = track.attach();
                        audioElement.id = `track-${track.sid}`;
                        document.body.appendChild(audioElement);

                        // Fix for event name mismatch
                        (track as any).on('unsubscribed', () => {
                            audioElement.remove();
                        });
                    }
                })
                .on(RoomEvent.DataReceived, (payload: Uint8Array) => {
                    try {
                        const decoder = new TextDecoder();
                        const data = JSON.parse(decoder.decode(payload));

                        if (data.type === 'voice_state') {
                            console.log('[LiveKit] Received state update:', data.state);
                            this.emitState(data.state);
                        }
                    } catch (error) {
                        console.error('[LiveKit] Failed to parse data message:', error);
                    }
                });

            await this.room.connect(this.livekitConfig.url, token);
            return true;
        } catch (error) {
            console.error('[LiveKit] Room connection failed:', error);
            this.emitState('error', { error: String(error) });
            return false;
        }
    }

    /**
     * Check if connected to LiveKit room
     */
    isRoomConnected(): boolean {
        return this.isConnected;
    }

    /**
     * Initialize audio and connect to LiveKit room
     */
    async initialize(): Promise<boolean> {
        try {
            // 1. Get microphone permission and setup local audio
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });

            this.audioContext = new AudioContext({ sampleRate: 16000 });
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            source.connect(this.analyser);

            this.setupVAD();

            // 2. Fetch connection token from backend
            console.log('[LiveKit] Fetching connection token...');
            const tokenResponse = await fetch(`${API_CONFIG.BASE_URL}/api/voice/token`);
            if (!tokenResponse.ok) {
                throw new Error(`Failed to fetch LiveKit token: ${tokenResponse.status}`);
            }

            const { token, url } = await tokenResponse.json();

            // 3. Connect to LiveKit room
            this.livekitConfig.url = url;
            const connected = await this.connectToRoom(token);

            if (connected && this.room) {
                // Publish local audio track
                const tracks = await this.room.localParticipant.publishTrack(
                    this.mediaStream.getAudioTracks()[0]
                );
                console.log('[LiveKit] Local audio track published');
            }

            console.log('[LiveKit] Voice service fully initialized');
            return true;
        } catch (error) {
            console.error('[LiveKit] Initialization failed:', error);
            this.emitState('error', { error: String(error) });
            return false;
        }
    }

    /**
     * Setup Voice Activity Detection
     */
    private setupVAD(): void {
        if (!this.audioContext || !this.analyser) return;

        // Create script processor for VAD (deprecated but widely supported)
        this.vadProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);

        this.vadProcessor.onaudioprocess = (event) => {
            if (!this.isListening) return;

            const inputData = event.inputBuffer.getChannelData(0);
            const audioLevel = this.calculateRMS(inputData);

            // Notify audio handlers for visualization
            this.audioHandlers.forEach(handler => handler(inputData));

            // Voice activity detection
            if (audioLevel > this.vadThreshold) {
                // Voice detected - reset silence timer
                this.clearSilenceTimer();

                if (this.currentState !== 'listening') {
                    this.emitState('listening', { audioLevel });
                }
            } else {
                // Silence detected - start timer if listening
                if (this.currentState === 'listening' && !this.silenceTimer) {
                    this.silenceTimer = setTimeout(() => {
                        this.onSilenceDetected();
                    }, this.vadSilenceTimeout);
                }
            }
        };

        this.analyser.connect(this.vadProcessor);
        this.vadProcessor.connect(this.audioContext.destination);
    }

    /**
     * Calculate RMS (Root Mean Square) for audio level
     */
    private calculateRMS(audioData: Float32Array): number {
        let sum = 0;
        for (let i = 0; i < audioData.length; i++) {
            sum += audioData[i] * audioData[i];
        }
        return Math.sqrt(sum / audioData.length);
    }

    /**
     * Handle silence detection (end of speech)
     */
    private onSilenceDetected(): void {
        this.clearSilenceTimer();

        if (this.currentState === 'listening') {
            // Transition to processing state
            this.emitState('processing');
        }
    }

    /**
     * Start listening for voice input
     */
    async startListening(): Promise<void> {
        if (!this.audioContext) {
            const initialized = await this.initialize();
            if (!initialized) return;
        }

        // Resume audio context if suspended
        if (this.audioContext?.state === 'suspended') {
            await this.audioContext.resume();
        }

        this.isListening = true;
        this.emitState('listening');
    }

    /**
     * Stop listening
     */
    stopListening(): void {
        this.isListening = false;
        this.clearSilenceTimer();
        this.emitState('idle');
    }

    /**
     * Play TTS audio response
     */
    async playTTS(audioData: ArrayBuffer): Promise<void> {
        // Create AudioContext for playback if needed (doesn't require microphone)
        if (!this.audioContext) {
            this.audioContext = new AudioContext({ sampleRate: 24000 });
        }

        // Resume audio context if suspended (browser policy)
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }

        try {
            this.isSpeaking = true;
            this.emitState('speaking');

            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(audioData.slice(0));

            // Create buffer source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            // Track playback completion
            source.onended = () => {
                this.isSpeaking = false;
                this.emitState('idle');
            };

            source.start(0);
        } catch (error) {
            console.error('[LiveKit] TTS playback failed:', error);
            this.isSpeaking = false;
            this.emitState('error', { error: String(error) });
            throw error;
        }
    }

    /**
     * Fetch and play TTS from backend
     */
    async speakText(text: string): Promise<void> {
        try {
            this.emitState('processing');

            const response = await fetch(`${API_CONFIG.BASE_URL}/api/speech/synthesize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    voice: this.ttsConfig.voice,
                    speed: this.ttsConfig.speed
                })
            });

            if (!response.ok) {
                throw new Error(`TTS request failed: ${response.status}`);
            }

            const data = await response.json();

            // Decode base64 audio
            const audioBytes = Uint8Array.from(atob(data.audio), c => c.charCodeAt(0));
            await this.playTTS(audioBytes.buffer);

        } catch (error) {
            console.error('[LiveKit] TTS synthesis failed:', error);
            this.emitState('error', { error: String(error) });
        }
    }

    /**
     * Get current audio level for visualization
     */
    getAudioLevel(): number {
        if (!this.analyser) return 0;

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteTimeDomainData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            const value = (dataArray[i] - 128) / 128;
            sum += value * value;
        }
        return Math.sqrt(sum / dataArray.length);
    }

    // ============================================
    // Event Handling
    // ============================================

    private emitState(state: VoiceState, metadata?: VoiceStateEvent['metadata']): void {
        this.currentState = state;
        const event: VoiceStateEvent = {
            state,
            timestamp: Date.now(),
            metadata
        };
        this.stateHandlers.forEach(handler => handler(event));
    }

    private clearSilenceTimer(): void {
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }
    }

    /**
     * Subscribe to voice state changes
     */
    onStateChange(handler: VoiceStateHandler): () => void {
        this.stateHandlers.push(handler);
        return () => {
            const index = this.stateHandlers.indexOf(handler);
            if (index > -1) this.stateHandlers.splice(index, 1);
        };
    }

    /**
     * Subscribe to audio data (for visualization)
     */
    onAudioData(handler: AudioDataHandler): () => void {
        this.audioHandlers.push(handler);
        return () => {
            const index = this.audioHandlers.indexOf(handler);
            if (index > -1) this.audioHandlers.splice(index, 1);
        };
    }

    /**
     * Get current voice state
     */
    getState(): VoiceState {
        return this.currentState;
    }

    /**
     * Set TTS configuration
     */
    setTTSConfig(config: Partial<TTSConfig>): void {
        this.ttsConfig = { ...this.ttsConfig, ...config };
    }

    /**
     * Cleanup resources
     */
    destroy(): void {
        this.stopListening();

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.analyser = null;
        this.vadProcessor = null;
        this.stateHandlers = [];
        this.audioHandlers = [];
    }
}

// Export singleton instance
export const voiceService = new LiveKitVoiceService();
