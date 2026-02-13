/**
 * useVoice Hook - React integration for LiveKit Voice Service
 * Provides voice state management, audio controls, and wake word detection
 * 
 * Phase 3: Voice-First Integration (Production)
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { voiceService, VoiceState, VoiceStateEvent } from '@/services/livekit.service';

export interface UseVoiceOptions {
    autoInitialize?: boolean;
    enableWakeWord?: boolean;
    onStateChange?: (state: VoiceState) => void;
    onWakeWord?: () => void;
    onError?: (error: string) => void;
}

export interface UseVoiceReturn {
    // State
    voiceState: VoiceState;
    isInitialized: boolean;
    isListening: boolean;
    isSpeaking: boolean;
    isProcessing: boolean;
    audioLevel: number;
    wakeWordDetected: boolean;

    // Controls
    initialize: () => Promise<boolean>;
    startListening: () => Promise<void>;
    stopListening: () => void;
    speak: (text: string) => Promise<void>;
    startWakeWordDetection: () => Promise<void>;
    stopWakeWordDetection: () => void;

    // Cleanup
    destroy: () => void;
}

// Wake word configuration
const WAKE_WORD = "hey aizen";
const WAKE_WORD_VARIANTS = ["hey aizen", "hey izen", "hey azon", "aizen"];

/**
 * React hook for voice interaction with AIZEN
 * Connects the UI to the LiveKit voice service with real-time state updates
 * Includes "Hey Aizen" wake word detection
 */
export const useVoice = (options: UseVoiceOptions = {}): UseVoiceReturn => {
    const {
        autoInitialize = false,
        enableWakeWord = false,
        onStateChange,
        onWakeWord,
        onError
    } = options;

    const [voiceState, setVoiceState] = useState<VoiceState>('idle');
    const [isInitialized, setIsInitialized] = useState(false);
    const [audioLevel, setAudioLevel] = useState(0);
    const [wakeWordDetected, setWakeWordDetected] = useState(false);

    const audioLevelInterval = useRef<NodeJS.Timeout | null>(null);
    const unsubscribeRef = useRef<(() => void) | null>(null);
    const wakeWordListenerRef = useRef<SpeechRecognition | null>(null);
    const isWakeWordActive = useRef(false);

    // Handle voice state changes from service
    const handleStateChange = useCallback((event: VoiceStateEvent) => {
        setVoiceState(event.state);
        onStateChange?.(event.state);

        if (event.state === 'error' && event.metadata?.error) {
            onError?.(event.metadata.error);
        }

        // Reset wake word when returning to idle
        if (event.state === 'idle') {
            setWakeWordDetected(false);
        }
    }, [onStateChange, onError]);

    // Initialize voice service
    const initialize = useCallback(async (): Promise<boolean> => {
        if (isInitialized) return true;

        try {
            const success = await voiceService.initialize();

            if (success) {
                // Subscribe to state changes
                unsubscribeRef.current = voiceService.onStateChange(handleStateChange);
                setIsInitialized(true);

                // Start audio level monitoring
                audioLevelInterval.current = setInterval(() => {
                    setAudioLevel(voiceService.getAudioLevel());
                }, 50);  // 50ms for smooth animation
            }

            return success;
        } catch (error) {
            console.error('[useVoice] Initialization failed:', error);
            onError?.(String(error));
            return false;
        }
    }, [isInitialized, handleStateChange, onError]);

    // Start wake word detection using Web Speech API
    const startWakeWordDetection = useCallback(async (): Promise<void> => {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('[useVoice] Web Speech API not supported');
            return;
        }

        try {
            // Create speech recognition instance
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();

            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onresult = (event: SpeechRecognitionEvent) => {
                const results = event.results;

                // Check last result for wake word
                for (let i = event.resultIndex; i < results.length; i++) {
                    const transcript = results[i][0].transcript.toLowerCase().trim();

                    // Check for wake word variants
                    const detected = WAKE_WORD_VARIANTS.some(variant =>
                        transcript.includes(variant)
                    );

                    if (detected) {
                        console.log('[useVoice] Wake word detected!', transcript);
                        setWakeWordDetected(true);
                        setVoiceState('listening');  // Immediate UI feedback
                        onWakeWord?.();

                        // Stop passive listening, activate full voice
                        recognition.stop();

                        // Start active listening
                        voiceService.startListening();
                    }
                }
            };

            recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
                console.error('[useVoice] Wake word error:', event.error);
                if (event.error !== 'no-speech') {
                    onError?.(event.error);
                }
            };

            recognition.onend = () => {
                // Restart if still in wake word mode
                if (isWakeWordActive.current && !wakeWordDetected) {
                    recognition.start();
                }
            };

            wakeWordListenerRef.current = recognition;
            isWakeWordActive.current = true;
            recognition.start();

            console.log('[useVoice] Wake word detection started');
        } catch (error) {
            console.error('[useVoice] Wake word setup failed:', error);
            onError?.(String(error));
        }
    }, [onWakeWord, onError, wakeWordDetected]);

    // Stop wake word detection
    const stopWakeWordDetection = useCallback((): void => {
        isWakeWordActive.current = false;
        if (wakeWordListenerRef.current) {
            wakeWordListenerRef.current.stop();
            wakeWordListenerRef.current = null;
        }
        console.log('[useVoice] Wake word detection stopped');
    }, []);

    // Start listening
    const startListening = useCallback(async (): Promise<void> => {
        if (!isInitialized) {
            const success = await initialize();
            if (!success) return;
        }

        // Stop wake word detection when starting active listening
        stopWakeWordDetection();

        await voiceService.startListening();
    }, [isInitialized, initialize, stopWakeWordDetection]);

    // Stop listening
    const stopListening = useCallback((): void => {
        voiceService.stopListening();
    }, []);

    // Speak text using TTS (doesn't require full voice initialization)
    const speak = useCallback(async (text: string): Promise<void> => {
        // speakText can work independently - it just calls the TTS endpoint
        // No need for full voice initialization (which requires microphone)
        try {
            await voiceService.speakText(text);
        } catch (error) {
            console.error('[useVoice] Speak failed:', error);
            throw error;
        }
    }, []);

    // Cleanup
    const destroy = useCallback((): void => {
        if (audioLevelInterval.current) {
            clearInterval(audioLevelInterval.current);
            audioLevelInterval.current = null;
        }

        if (unsubscribeRef.current) {
            unsubscribeRef.current();
            unsubscribeRef.current = null;
        }

        stopWakeWordDetection();

        voiceService.destroy();
        setIsInitialized(false);
        setVoiceState('idle');
        setWakeWordDetected(false);
    }, [stopWakeWordDetection]);

    // Auto-initialize if requested
    useEffect(() => {
        if (autoInitialize) {
            initialize();
        }

        if (enableWakeWord) {
            startWakeWordDetection();
        }

        return () => {
            if (audioLevelInterval.current) {
                clearInterval(audioLevelInterval.current);
            }
            if (unsubscribeRef.current) {
                unsubscribeRef.current();
            }
            stopWakeWordDetection();
        };
    }, [autoInitialize, enableWakeWord, initialize, startWakeWordDetection, stopWakeWordDetection]);

    return {
        voiceState,
        isInitialized,
        isListening: voiceState === 'listening',
        isSpeaking: voiceState === 'speaking',
        isProcessing: voiceState === 'processing',
        audioLevel,
        wakeWordDetected,
        initialize,
        startListening,
        stopListening,
        speak,
        startWakeWordDetection,
        stopWakeWordDetection,
        destroy
    };
};

// Web Speech API Type Declarations
interface SpeechRecognitionEventMap {
    result: SpeechRecognitionEvent;
    error: SpeechRecognitionErrorEvent;
    end: Event;
    start: Event;
}

interface SpeechRecognitionEvent extends Event {
    resultIndex: number;
    results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
    error: string;
    message: string;
}

interface SpeechRecognitionResultList {
    length: number;
    item(index: number): SpeechRecognitionResult;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
    isFinal: boolean;
    length: number;
    item(index: number): SpeechRecognitionAlternative;
    [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
}

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    maxAlternatives: number;
    start(): void;
    stop(): void;
    abort(): void;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
    onend: (() => void) | null;
    onstart: (() => void) | null;
}

interface SpeechRecognitionConstructor {
    new(): SpeechRecognition;
}

declare global {
    interface Window {
        SpeechRecognition: SpeechRecognitionConstructor;
        webkitSpeechRecognition: SpeechRecognitionConstructor;
    }
}

