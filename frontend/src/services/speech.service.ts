/**
 * Speech Service - Handles speech-to-text and text-to-speech
 */

import { apiClient } from '@/lib/api-client';
import { API_CONFIG } from '@/config/api.config';
import type {
    TranscribeRequest,
    TranscribeResponse,
    SynthesizeRequest,
} from '@/types/api.types';

export const speechService = {
    /**
     * Transcribe audio to text (Speech-to-Text)
     */
    async transcribe(audio: Blob | File, language?: string) {
        const formData = new FormData();
        formData.append('audio', audio);
        if (language) {
            formData.append('language', language);
        }

        return apiClient.upload<TranscribeResponse>(
            API_CONFIG.ENDPOINTS.SPEECH_TRANSCRIBE,
            formData
        );
    },

    /**
     * Synthesize text to speech (Text-to-Speech)
     */
    async synthesize(text: string, voice?: string, speed?: number) {
        const request: SynthesizeRequest = {
            text,
            voice,
            speed,
        };

        // This returns audio blob
        const blob = await apiClient.download(API_CONFIG.ENDPOINTS.SPEECH_SYNTHESIZE);
        return blob;
    },
};
