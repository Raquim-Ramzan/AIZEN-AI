import { Send, Camera, Paperclip, X } from "lucide-react";
import { useState } from "react";

interface InputBarProps {
    onSend: (message: string, attachedFile?: File | null) => void;
    onScreenCapture: () => void;
    onFileAttach?: (file: File) => void;
}

export const InputBar = ({ onSend, onScreenCapture, onFileAttach }: InputBarProps) => {
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

            <div className="flex items-end space-x-3">
                {/* Text input */}
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={attachedFile ? "Describe what you want to know about this file..." : "Enter command or question..."}
                    className="flex-1 bg-muted/60 border-2 border-primary/30 rounded-lg px-4 py-3 text-foreground font-quantico text-sm resize-none focus:outline-none focus:border-primary focus:shadow-[0_0_20px_rgba(0,217,255,0.3)] transition-all placeholder:text-muted-foreground"
                    rows={1}
                    style={{ minHeight: "48px", maxHeight: "120px" }}
                />

                {/* Send button */}
                <button
                    onClick={handleSend}
                    disabled={!input.trim() && !attachedFile}
                    className="px-6 py-3 bg-primary/10 border-2 border-primary rounded-lg text-primary font-aldrich text-sm tracking-wider uppercase transition-all duration-300 hover:bg-primary hover:text-black hover:-translate-y-1 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:bg-primary/10 disabled:hover:text-primary box-glow-cyan"
                >
                    <Send className="w-5 h-5 inline mr-2" />
                    SEND
                </button>

                {/* Screen capture button */}
                <button
                    onClick={onScreenCapture}
                    className="px-6 py-3 bg-accent/10 border-2 border-accent rounded-lg text-accent font-aldrich text-sm tracking-wider uppercase transition-all duration-300 hover:bg-accent hover:text-black hover:-translate-y-1 box-glow-green"
                >
                    <Camera className="w-5 h-5 inline mr-2" />
                    SCREEN
                </button>

                {/* File attach button */}
                <label className="px-6 py-3 bg-warning/10 border-2 border-warning rounded-lg text-warning font-aldrich text-sm tracking-wider uppercase transition-all duration-300 hover:bg-warning hover:text-black hover:-translate-y-1 cursor-pointer box-glow-orange">
                    <Paperclip className="w-5 h-5 inline mr-2" />
                    FILE
                    <input
                        type="file"
                        onChange={handleFileSelect}
                        className="hidden"
                        accept="image/*,.pdf,.txt,.md,.json,.py,.js,.ts,.html,.css"
                    />
                </label>
            </div>
        </div>
    );
};
