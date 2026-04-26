import { Send, Camera, Paperclip, X, Mic, MicOff } from "lucide-react";
import { useState } from "react";

interface InputBarProps {
    onSend: (message: string, attachedFile?: File | null) => void;
    onScreenCapture: () => void;
    onFileAttach?: (file: File) => void;
    onVoiceToggle?: () => void;
    isListening?: boolean;
}

export const InputBar = ({ onSend, onScreenCapture, onFileAttach, onVoiceToggle, isListening }: InputBarProps) => {
    const [input, setInput] = useState("");
    const [attachedFile, setAttachedFile] = useState<File | null>(null);

    const handleSend = () => {
        if (input.trim() || attachedFile) {
            // Send message WITH the attached file
            onSend(input, attachedFile);
            setInput("");
            setAttachedFile(null);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setAttachedFile(file);
            onFileAttach?.(file);
        }
        // Reset the input so the same file can be selected again
        e.target.value = '';
    };

    const removeAttachedFile = () => {
        setAttachedFile(null);
    };

    return (
        <div className="border-t border-primary bg-card/95 backdrop-blur-md p-6" style={{ boxShadow: "0 -2px 20px rgba(0, 217, 255, 0.2)" }}>
            {/* File preview */}
            {attachedFile && (
                <div className="mb-4 p-3 bg-warning/10 border border-warning rounded-lg flex items-center justify-between animate-slide-in-left">
                    <div className="flex items-center space-x-2">
                        <Paperclip className="w-4 h-4 text-warning" />
                        <span className="text-sm font-quantico text-warning">{attachedFile.name}</span>
                        <span className="text-xs text-muted-foreground">
                            ({(attachedFile.size / 1024).toFixed(1)} KB)
                        </span>
                    </div>
                    <button
                        onClick={removeAttachedFile}
                        className="text-warning hover:text-warning/70 transition-colors p-1"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            <div className="flex items-center space-x-2">
                {/* Text input */}
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={attachedFile ? "Describe what you want to know about this file..." : "Enter command or question..."}
                    className="flex-1 min-w-[200px] bg-muted/60 border-2 border-primary/30 rounded-xl px-4 py-3 text-foreground font-quantico text-sm resize-none focus:outline-none focus:border-primary focus:shadow-[0_0_20px_rgba(0,217,255,0.3)] transition-all placeholder:text-muted-foreground"
                    rows={1}
                    style={{ minHeight: "52px", maxHeight: "150px" }}
                />

                {/* Utility Buttons Group */}
                <div className="flex items-center space-x-2 bg-black/20 p-1 rounded-xl border border-white/5">
                    {/* Voice button */}
                    <button
                        onClick={onVoiceToggle}
                        title={isListening ? "Stop Listening" : "Voice Input"}
                        className={`p-3 border-2 rounded-lg transition-all duration-300 ${isListening
                                ? "bg-red-500/20 border-red-500 text-red-500 box-glow-red animate-pulse"
                                : "bg-primary/5 border-primary/20 text-primary/70 hover:text-primary hover:border-primary"
                            }`}
                    >
                        {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </button>

                    {/* Screen capture button */}
                    <button
                        onClick={onScreenCapture}
                        title="Screen Capture"
                        className="p-3 bg-accent/5 border-2 border-accent/20 rounded-lg text-accent/70 hover:text-accent hover:border-accent transition-all duration-300"
                    >
                        <Camera className="w-5 h-5" />
                    </button>

                    {/* File attach button */}
                    <label 
                        title="Attach File"
                        className="p-3 bg-warning/5 border-2 border-warning/20 rounded-lg text-warning/70 hover:text-warning hover:border-warning transition-all duration-300 cursor-pointer"
                    >
                        <Paperclip className="w-5 h-5" />
                        <input
                            type="file"
                            onChange={handleFileSelect}
                            className="hidden"
                            accept="image/*,audio/*,.pdf,.txt,.md,.json,.py,.js,.ts,.html,.css"
                        />
                    </label>
                </div>

                {/* Send button */}
                <button
                    onClick={handleSend}
                    disabled={!input.trim() && !attachedFile}
                    className="px-6 py-3 h-[52px] bg-primary/10 border-2 border-primary rounded-xl text-primary font-aldrich text-sm tracking-wider uppercase transition-all duration-300 hover:bg-primary hover:text-black disabled:opacity-30 disabled:cursor-not-allowed box-glow-cyan flex items-center"
                >
                    <Send className="w-5 h-5 mr-2" />
                    <span className="hidden md:inline">SEND</span>
                </button>
            </div>
        </div>
    );
};
