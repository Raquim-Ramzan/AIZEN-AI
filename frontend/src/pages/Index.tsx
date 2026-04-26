import { useState, useEffect, useCallback, useRef } from "react";
import { BackgroundEffects } from "@/components/BackgroundEffects";
import { HolographicSphere } from "@/components/HolographicSphere";
import { Sidebar } from "@/components/Sidebar";
import { ChatInterface } from "@/components/ChatInterface";
import { InputBar } from "@/components/InputBar";
import { SettingsPanel } from "@/components/SettingsPanel";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { MemoryIndicator } from "@/components/MemoryIndicator";
import { OfflineFallback } from "@/components/OfflineFallback";
import { ArtifactsPanel, Artifact } from "@/components/ArtifactsPanel";
import { SystemOperationApproval } from "@/components/SystemOperationApproval";
import { Button } from "@/components/ui/button";
import { Layout } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

// Backend integration hooks
import { useChat } from "@/hooks/useChat";
import { useSessions } from "@/hooks/useSessions";
import { useBackendConnection } from "@/hooks/useBackendConnection";
import { useVoice } from "@/hooks/useVoice";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

type SphereState = "idle" | "hover" | "listening" | "processing" | "speaking" | "error";

const Index = () => {
    // Backend connectivity
    const { connectionState, checkHealth } = useBackendConnection();
    const {
        sessions,
        activeSessionId,
        createSession,
        deleteSession,
        renameSession,
        selectSession,
        setActiveSession,
        clearActiveSession,
        refetch: refetchSessions,
    } = useSessions();

    const {
        messages,
        isStreaming,
        error: chatError,
        pendingOperation,
        activeConversationId,
        sendMessage: sendChatMessage,
        clearMessages,
        clearPendingOperation,
        resetForNewConversation,
        createNewSession,
    } = useChat(activeSessionId, {
        onConversationCreated: (conversationId) => {
            // Backend created a new conversation, update the session list
            console.log('[Index] New conversation created:', conversationId);
            setActiveSession(conversationId);
            refetchSessions();
        },
    });

    // UI-specific state (not backend-related)
    const [sphereState, setSphereState] = useState<SphereState>("idle");
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [isLearning, setIsLearning] = useState(false);

    // Model selection state
    const [selectedProvider, setSelectedProvider] = useState<string | undefined>();
    const [selectedModel, setSelectedModel] = useState<string | undefined>();

    // NEW: Artifacts state
    const [artifactsOpen, setArtifactsOpen] = useState(false);
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [activeArtifactId, setActiveArtifactId] = useState<string | undefined>();

    // Auto-speak state (persisted to localStorage)
    const [autoSpeak, setAutoSpeak] = useState(() => {
        const saved = localStorage.getItem('aizen-autospeak');
        return saved ? JSON.parse(saved) : false;
    });

    // Voice service integration (Phase 3: Event-Driven)
    const {
        voiceState,
        isInitialized: voiceInitialized,
        startListening,
        stopListening,
        speak,
        audioLevel
    } = useVoice({
        onStateChange: (state) => {
            // Sync voice state with sphere state
            setSphereState(state);
        },
        onError: (error) => {
            toast.error("Voice Error", { description: error });
            setSphereState("error");
            setTimeout(() => setSphereState("idle"), 2000);
        }
    });

    const prevStreamingRef = useRef(false);

    const handleSphereActivate = useCallback(async () => {
        if (sphereState === "idle") {
            // Real voice activation via LiveKit
            await startListening();
            toast.info("Voice input activated", {
                description: "Listening for your command...",
            });
        } else if (sphereState === "listening") {
            // Stop listening
            stopListening();
        } else {
            setSphereState("idle");
        }
    }, [sphereState, startListening, stopListening]);

    const handleSendMessage = async (content: string, attachedFile?: File | null) => {
        // Update sphere state to processing
        setSphereState("processing");

        // Build metadata with model selection (strict typing)
        interface SendMetadata {
            temperature: number;
            model_provider?: string;
            model_model?: string;
            attached_file?: {
                name: string;
                type: string;
                size: number;
                data: string;
            };
        }

        const metadata: SendMetadata = {
            temperature: 0.7,
        };

        // Add model selection if user chose specific provider/model
        if (selectedProvider && selectedProvider !== 'auto') {
            metadata.model_provider = selectedProvider;
        }
        if (selectedModel && selectedModel !== 'auto') {
            metadata.model_model = selectedModel;
        }

        // If file is attached, convert to base64 and add to metadata
        if (attachedFile) {
            try {
                const base64Data = await fileToBase64(attachedFile);
                metadata.attached_file = {
                    name: attachedFile.name,
                    type: attachedFile.type,
                    size: attachedFile.size,
                    data: base64Data,
                };
                toast.info("Processing image...", {
                    description: `Sending ${attachedFile.name} to AI for analysis`,
                });
            } catch (error) {
                console.error('[Index] Error converting file to base64:', error);
                toast.error("Failed to process file", {
                    description: "Could not read the attached file",
                });
            }
        }

        // Send message to backend via WebSocket with metadata
        const success = await sendChatMessage(content || "What is this?", metadata);

        if (!success) {
            setSphereState("error");
            toast.error("Failed to send message", {
                description: "Could not connect to AI backend",
            });
            setTimeout(() => setSphereState("idle"), 2000);
            return;
        }

        // Simulate memory learning during response
        setIsLearning(true);
        setTimeout(() => {
            setIsLearning(false);
        }, 2000);
    };

    // Helper function to convert file to base64
    const fileToBase64 = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => {
                const result = reader.result as string;
                // Remove the data:mime/type;base64, prefix
                const base64 = result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = (error) => reject(error);
        });
    };

    // Handle model selection from settings
    const handleModelChange = (provider?: string, model?: string) => {
        setSelectedProvider(provider);
        setSelectedModel(model);

        if (!provider || provider === 'auto') {
            toast.info("Model selection", {
                description: "Using automatic model selection",
            });
        } else {
            toast.info("Model selection", {
                description: `Using ${provider}${model ? ` / ${model}` : ''}`,
            });
        }
    };

    const handleScreenCapture = () => {
        toast.info("Screen capture initiated", {
            description: "Analyzing visual data...",
        });
    };

    const handleFileAttach = (file: File) => {
        toast.success("File attached", {
            description: `${file.name} ready to upload`,
        });
    };

    const handleNewSession = async () => {
        // Clear the current session and create a new one via WebSocket
        clearActiveSession();
        clearMessages();
        setArtifacts([]);

        // Send request to backend to create new session
        const created = createNewSession();

        if (created) {
            toast.success("New chat started", {
                description: "Ready for a new conversation",
            });
            // Refetch sessions to show the new one
            refetchSessions();
        } else {
            toast.error("Failed to start new chat", {
                description: "Check connection and try again",
            });
        }
    };

    const handleSessionSelect = (id: string) => {
        selectSession(id);
        toast.info("Session loaded");
        // Artifacts will be re-extracted from loaded messages automatically via useEffect
    };

    const handleSessionDelete = async (id: string) => {
        try {
            await deleteSession(id);
            toast.success("Session deleted");
        } catch (error) {
            toast.error("Failed to delete session");
        }
    };

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    const exitFullscreen = () => {
        if (document.fullscreenElement) {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    // System operation approval handlers
    const handleApproveOperation = async (operationId: string, remember: boolean) => {
        try {
            const response = await fetch(`${API_URL}/api/system/approve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    operation_id: operationId,
                    approved: true,
                    remember
                })
            });

            if (!response.ok) {
                throw new Error("Failed to approve operation");
            }

            toast.success("Operation approved", {
                description: "The system operation is now executing"
            });

            clearPendingOperation();
        } catch (error) {
            toast.error("Failed to approve operation", {
                description: error instanceof Error ? error.message : "Unknown error"
            });
        }
    };

    const handleDenyOperation = async (operationId: string) => {
        try {
            const response = await fetch(`${API_URL}/api/system/approve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    operation_id: operationId,
                    approved: false,
                    remember: false
                })
            });

            if (!response.ok) {
                throw new Error("Failed to deny operation");
            }

            toast.info("Operation denied");
            clearPendingOperation();
        } catch (error) {
            toast.error("Failed to deny operation", {
                description: error instanceof Error ? error.message : "Unknown error"
            });
        }
    };

    // -- Lifecycle Hooks (Moved here to avoid TDZ) --

    // Extract artifacts from messages
    useEffect(() => {
        const newArtifacts: Artifact[] = [];

        messages.forEach(msg => {
            if (msg.role === 'assistant') {
                // Regex to find code blocks: ```language code ```
                const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
                let match;
                let index = 0;

                while ((match = codeBlockRegex.exec(msg.content)) !== null) {
                    const language = match[1] || 'text';
                    const code = match[2];
                    const title = `${language} snippet ${index + 1}`;
                    const id = `art-${msg.id}-${index}`;

                    newArtifacts.push({
                        id,
                        title,
                        type: 'code',
                        content: code,
                        language,
                        timestamp: Date.now() // In real app, use msg timestamp
                    });
                    index++;
                }
            }
        });

        // Only update if count changed to avoid loops (simple check)
        if (newArtifacts.length !== artifacts.length) {
            setArtifacts(newArtifacts);
            // Notify if new artifact found during streaming
            if (isStreaming && newArtifacts.length > artifacts.length) {
                toast.success("New artifact created", {
                    description: "Code snippet saved to Artifacts panel",
                    action: {
                        label: "View",
                        onClick: () => setArtifactsOpen(true)
                    }
                });
            }
        }
    }, [messages, isStreaming, artifacts.length]);

    // Update sphere state based on streaming status
    useEffect(() => {
        if (isStreaming) {
            setSphereState("speaking");
        } else if (!isStreaming && sphereState === "speaking") {
            setSphereState("idle");
        }
    }, [isStreaming, sphereState]);

    // Show chat errors
    useEffect(() => {
        if (chatError) {
            toast.error("Chat Error", {
                description: chatError,
            });
        }
    }, [chatError]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Alt + PgUp - Activate voice
            if (e.altKey && e.key === "PageUp") {
                e.preventDefault();
                handleSphereActivate();
            }

            // F11 - Fullscreen
            if (e.key === "F11") {
                e.preventDefault();
                toggleFullscreen();
            }

            // ESC - Exit fullscreen or stop listening
            if (e.key === "Escape") {
                if (isFullscreen) {
                    exitFullscreen();
                } else if (sphereState === "listening") {
                    setSphereState("idle");
                }
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [sphereState, isFullscreen, handleSphereActivate, toggleFullscreen, exitFullscreen]);

    // Auto-speak effect: speaks AI responses when enabled
    useEffect(() => {
        if (isStreaming) {
            prevStreamingRef.current = true;
        } else if (!isStreaming && prevStreamingRef.current) {
            // Streaming just completed
            prevStreamingRef.current = false;

            console.log('[Index] Streaming completed, autoSpeak:', autoSpeak, 'messages:', messages.length);

            // Auto-speak the last assistant message if enabled
            if (autoSpeak && messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                if (lastMessage.role === 'assistant' && lastMessage.content) {
                    // Extract text content (remove code blocks for cleaner speech)
                    const textToSpeak = lastMessage.content
                        .replace(/```[\s\S]*?```/g, ' ')
                        .replace(/`[^`]+`/g, (match) => match.slice(1, -1))
                        .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold markdown
                        .replace(/\*([^*]+)\*/g, '$1')      // Remove italic markdown
                        .replace(/#{1,6}\s+/g, '')          // Remove headings
                        .replace(/\n+/g, '. ')              // Convert newlines to pauses
                        .trim();

                    if (textToSpeak.length > 0 && textToSpeak.length < 3000) {
                        console.log('[Index] Auto-speaking response:', textToSpeak.substring(0, 100) + '...');

                        // Try to speak using the voice service
                        speak(textToSpeak).catch((error) => {
                            console.error('[Index] Auto-speak failed:', error);
                            // Fallback to browser's native Speech Synthesis
                            if ('speechSynthesis' in window) {
                                const utterance = new SpeechSynthesisUtterance(textToSpeak);
                                utterance.rate = 1.0;
                                utterance.pitch = 1.0;
                                window.speechSynthesis.speak(utterance);
                            }
                        });
                    }
                }
            }
        }
    }, [isStreaming, messages, autoSpeak, speak]);

    // Show offline fallback if backend is not connected
    if (connectionState === "error" || connectionState === "disconnected") {
        return (
            <div className="relative w-screen h-screen overflow-hidden bg-black">
                <BackgroundEffects />
                <div className="relative z-10 h-full">
                    <OfflineFallback onRetry={checkHealth} />
                </div>
            </div>
        );
    }

    return (
        <div className="relative w-screen h-screen overflow-hidden bg-black">
            {/* Background effects */}
            <BackgroundEffects />

            {/* Main layout */}
            <div className="relative z-10 flex h-full transition-all duration-300">
                {/* Left Sidebar */}
                <Sidebar
                    sessions={sessions}
                    activeSessionId={activeSessionId}
                    onSessionSelect={handleSessionSelect}
                    onSessionDelete={handleSessionDelete}
                    onNewSession={handleNewSession}
                    onSettingsClick={() => setSettingsOpen(true)}
                    onSessionRename={async (id, newTitle) => {
                        try {
                            await renameSession(id, newTitle);
                            toast.success("Conversation renamed");
                        } catch (error) {
                            toast.error("Failed to rename conversation");
                        }
                    }}
                />

                {/* Center Panel - Holographic Sphere */}
                <div className={`
                    flex items-center justify-center relative transition-all duration-500
                    ${artifactsOpen ? 'w-[400px]' : 'w-[600px]'}
                `}>
                    <HolographicSphere
                        state={sphereState}
                        onActivate={handleSphereActivate}
                        audioLevel={audioLevel}
                    />
                </div>

                {/* Right Panel - Chat Interface */}
                <div className="flex-1 flex flex-col relative min-w-0">
                    {/* Status indicators */}
                    <div className="absolute top-4 right-4 flex items-center gap-3 z-20">
                        {/* Artifact Toggle Button */}
                        {artifacts.length > 0 && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setArtifactsOpen(!artifactsOpen)}
                                className={`
                                    border-primary/30 backdrop-blur-md transition-all
                                    ${artifactsOpen ? 'bg-primary/20 text-accent' : 'bg-black/40 text-primary'}
                                `}
                            >
                                <Layout className="w-4 h-4 mr-2" />
                                Artifacts
                                <Badge variant="secondary" className="ml-2 h-5 min-w-[20px] px-1">
                                    {artifacts.length}
                                </Badge>
                            </Button>
                        )}
                        <ConnectionStatus status={connectionState} />
                    </div>

                    {/* Chat messages */}
                    <ChatInterface
                        messages={messages}
                        onArtifactClick={(id) => {
                            setActiveArtifactId(id);
                            setArtifactsOpen(true);
                        }}
                    />

                    {/* Input bar */}
                    <InputBar
                        onSend={handleSendMessage}
                        onScreenCapture={handleScreenCapture}
                        onFileAttach={handleFileAttach}
                        onVoiceToggle={handleSphereActivate}
                        isListening={sphereState === "listening"}
                    />
                </div>

                {/* Artifacts Panel (Right Sidebar) */}
                <ArtifactsPanel
                    isOpen={artifactsOpen}
                    onClose={() => setArtifactsOpen(false)}
                    artifacts={artifacts}
                    activeArtifactId={activeArtifactId}
                />
            </div>

            {/* Floating components */}
            <SettingsPanel
                isOpen={settingsOpen}
                onClose={() => setSettingsOpen(false)}
                onModelChange={handleModelChange}
                autoSpeak={autoSpeak}
                onAutoSpeakChange={setAutoSpeak}
            />
            <MemoryIndicator isLearning={isLearning} />

            {/* System Operation Approval Modal */}
            <SystemOperationApproval
                operation={pendingOperation}
                onApprove={handleApproveOperation}
                onDeny={handleDenyOperation}
                onClose={clearPendingOperation}
            />
        </div>
    );
};

export default Index;
