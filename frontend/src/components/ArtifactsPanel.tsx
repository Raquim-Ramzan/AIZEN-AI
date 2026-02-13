import { useState, useEffect } from "react";
import { X, Code, FileText, Copy, Download, Maximize2, Minimize2, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export interface Artifact {
    id: string;
    title: string;
    type: "code" | "text" | "html" | "image";
    content: string;
    language?: string;
    timestamp: number;
}

interface ArtifactsPanelProps {
    isOpen: boolean;
    onClose: () => void;
    artifacts: Artifact[];
    activeArtifactId?: string;
}

export const ArtifactsPanel = ({ isOpen, onClose, artifacts, activeArtifactId }: ArtifactsPanelProps) => {
    const [selectedId, setSelectedId] = useState<string | undefined>(activeArtifactId);
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Update selected artifact when activeArtifactId changes
    useEffect(() => {
        if (activeArtifactId) {
            setSelectedId(activeArtifactId);
        } else if (artifacts.length > 0 && !selectedId) {
            setSelectedId(artifacts[0].id);
        }
    }, [activeArtifactId, artifacts, selectedId]);

    const selectedArtifact = artifacts.find(a => a.id === selectedId);

    const handleCopy = () => {
        if (selectedArtifact) {
            navigator.clipboard.writeText(selectedArtifact.content);
            toast.success("Copied to clipboard");
        }
    };

    const handleDownload = () => {
        if (!selectedArtifact) return;

        const blob = new Blob([selectedArtifact.content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = selectedArtifact.title || "artifact.txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Download started");
    };

    if (!isOpen) return null;

    return (
        <div
            className={`
                fixed right-0 top-0 bottom-0 z-40 bg-black/95 border-l border-primary/30 backdrop-blur-xl
                transition-all duration-300 ease-in-out flex flex-col
                ${isFullscreen ? "w-screen" : "w-[600px]"}
                ${isOpen ? "translate-x-0" : "translate-x-full"}
            `}
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-primary/20">
                <div className="flex items-center gap-2">
                    <Code className="w-5 h-5 text-accent" />
                    <h2 className="text-lg font-orbitron font-bold text-primary tracking-wider">
                        ARTIFACTS
                    </h2>
                    <Badge variant="outline" className="ml-2 border-primary/30 text-primary/70">
                        {artifacts.length}
                    </Badge>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setIsFullscreen(!isFullscreen)}
                        className="text-primary hover:bg-primary/10"
                    >
                        {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onClose}
                        className="text-primary hover:bg-primary/10"
                    >
                        <ChevronRight className="w-5 h-5" />
                    </Button>
                </div>
            </div>

            {/* Content Layout */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar List (only visible if not fullscreen or if explicitly toggled) */}
                {!isFullscreen && (
                    <div className="w-48 border-r border-primary/20 flex flex-col bg-black/50">
                        <ScrollArea className="flex-1">
                            <div className="p-2 space-y-2">
                                {artifacts.map((artifact) => (
                                    <button
                                        key={artifact.id}
                                        onClick={() => setSelectedId(artifact.id)}
                                        className={`
                                            w-full text-left p-3 rounded-md text-sm transition-all
                                            border border-transparent
                                            ${selectedId === artifact.id
                                                ? "bg-primary/10 border-primary/30 text-accent"
                                                : "hover:bg-primary/5 text-muted-foreground hover:text-primary"}
                                        `}
                                    >
                                        <div className="font-medium truncate font-quantico">{artifact.title}</div>
                                        <div className="text-xs opacity-60 mt-1 flex items-center gap-1">
                                            {artifact.type === 'code' ? <Code className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
                                            {artifact.language || artifact.type}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </ScrollArea>
                    </div>
                )}

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col bg-black/30">
                    {selectedArtifact ? (
                        <>
                            {/* Toolbar */}
                            <div className="flex items-center justify-between p-3 border-b border-primary/10 bg-black/40">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-quantico text-accent">
                                        {selectedArtifact.title}
                                    </span>
                                    {selectedArtifact.language && (
                                        <Badge variant="secondary" className="text-xs bg-primary/10 text-primary border-0">
                                            {selectedArtifact.language}
                                        </Badge>
                                    )}
                                </div>
                                <div className="flex items-center gap-1">
                                    <Button variant="ghost" size="sm" onClick={handleCopy} className="h-8 text-xs gap-1">
                                        <Copy className="w-3 h-3" /> Copy
                                    </Button>
                                    <Button variant="ghost" size="sm" onClick={handleDownload} className="h-8 text-xs gap-1">
                                        <Download className="w-3 h-3" /> Save
                                    </Button>
                                </div>
                            </div>

                            {/* Code/Content View */}
                            <ScrollArea className="flex-1 p-4">
                                {selectedArtifact.type === 'code' ? (
                                    <pre className="font-mono text-sm text-primary/90 bg-black/50 p-4 rounded-lg border border-primary/10 overflow-x-auto">
                                        <code>{selectedArtifact.content}</code>
                                    </pre>
                                ) : (
                                    <div className="prose prose-invert max-w-none">
                                        {selectedArtifact.content}
                                    </div>
                                )}
                            </ScrollArea>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-muted-foreground flex-col gap-3">
                            <Code className="w-12 h-12 opacity-20" />
                            <p className="font-quantico">Select an artifact to view</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
