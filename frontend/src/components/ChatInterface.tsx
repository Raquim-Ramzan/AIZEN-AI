import { useEffect, useRef } from "react";
import { TypingIndicator } from "./TypingIndicator";
import { Terminal, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Message metadata with strict typing (no any) */
interface MessageMetadata {
    provider?: string;
    model?: string;
    tokens?: number;
    processingTime?: number;
}

export interface Message {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: string;
    isTyping?: boolean;
    metadata?: MessageMetadata;
}

interface ChatInterfaceProps {
    messages: Message[];
    onArtifactClick?: (artifactId: string) => void;
}

export const ChatInterface = ({ messages, onArtifactClick }: ChatInterfaceProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Helper to format provider name (e.g. "ModelProvider.GEMINI" -> "Gemini")
    const formatProvider = (provider: string) => {
        if (provider.includes('.')) {
            return provider.split('.')[1].charAt(0).toUpperCase() + provider.split('.')[1].slice(1).toLowerCase();
        }
        return provider.charAt(0).toUpperCase() + provider.slice(1);
    };

    // Helper to render message content with artifact buttons
    const renderContent = (message: Message) => {
        if (message.role !== 'assistant') return <p className="text-sm font-electrolize leading-relaxed">{message.content}</p>;

        const parts = [];
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        let lastIndex = 0;
        let match;
        let artifactIndex = 0;

        while ((match = codeBlockRegex.exec(message.content)) !== null) {
            // Add text before code block
            if (match.index > lastIndex) {
                parts.push(
                    <p key={`text-${lastIndex}`} className="text-sm font-electrolize leading-relaxed mb-3">
                        {message.content.slice(lastIndex, match.index)}
                    </p>
                );
            }

            // Add Artifact Button instead of code
            const language = match[1] || 'code';
            const artifactId = `art-${message.id}-${artifactIndex}`;

            parts.push(
                <div key={`art-${artifactIndex}`} className="my-3">
                    <Button
                        variant="outline"
                        className="w-full justify-between bg-black/40 border-primary/30 hover:bg-primary/10 hover:border-primary/60 group"
                        onClick={() => onArtifactClick?.(artifactId)}
                    >
                        <div className="flex items-center gap-2">
                            <div className="p-1 rounded bg-primary/10 text-primary group-hover:text-accent transition-colors">
                                <Terminal className="w-4 h-4" />
                            </div>
                            <span className="font-quantico text-primary/90">
                                {language.toUpperCase()} Snippet
                            </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground group-hover:text-primary transition-colors">
                            <span>View Artifact</span>
                            <ExternalLink className="w-3 h-3" />
                        </div>
                    </Button>
                </div>
            );

            lastIndex = match.index + match[0].length;
            artifactIndex++;
        }

        // Add remaining text
        if (lastIndex < message.content.length) {
            parts.push(
                <p key={`text-${lastIndex}`} className="text-sm font-electrolize leading-relaxed mt-3">
                    {message.content.slice(lastIndex)}
                </p>
            );
        }

        return parts.length > 0 ? <div>{parts}</div> : <p className="text-sm font-electrolize leading-relaxed">{message.content}</p>;
    };

    return (
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4 scrollbar-custom">
            {messages.map((message) => {
                if (message.role === "system") {
                    return (
                        <div
                            key={message.id}
                            className="w-full py-2 px-4 border-t border-b border-primary/20 bg-primary/5 text-center"
                        >
                            <p className="text-sm font-quantico text-muted-foreground">{message.content}</p>
                        </div>
                    );
                }

                const isUser = message.role === "user";

                // Show typing indicator for assistant messages that are typing
                if (message.isTyping && !isUser) {
                    return (
                        <div key={message.id} className="flex justify-start">
                            <TypingIndicator />
                        </div>
                    );
                }

                return (
                    <div
                        key={message.id}
                        className={`flex ${isUser ? "justify-end" : "justify-start"} animate-${isUser ? "slide-in-right" : "slide-in-left"
                            }`}
                    >
                        <div
                            className={`
                max-w-[70%] p-4 rounded-[18px] backdrop-blur-md
                ${isUser
                                    ? "bg-primary/10 border-2 border-primary text-foreground"
                                    : "bg-accent/8 border-2 border-accent text-foreground"
                                }
              `}
                            style={{
                                boxShadow: isUser
                                    ? "0 4px 20px rgba(0, 217, 255, 0.3)"
                                    : "0 4px 20px rgba(0, 255, 65, 0.3)",
                            }}
                        >
                            {renderContent(message)}

                            <div className="flex items-center justify-between mt-2 gap-2">
                                <p className="text-xs text-muted-foreground font-quantico">
                                    {message.timestamp}
                                </p>
                                {/* Display provider/model info for assistant messages */}
                                {!isUser && message.metadata?.provider && (
                                    <p className="text-xs text-accent font-quantico flex items-center gap-1">
                                        <span className="opacity-60">via</span>
                                        <span className="font-bold">{formatProvider(message.metadata.provider)}</span>
                                        {message.metadata.model && (
                                            <span className="opacity-60 text-[10px]">({message.metadata.model})</span>
                                        )}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                );
            })}
            <div ref={messagesEndRef} />
        </div>
    );
};
