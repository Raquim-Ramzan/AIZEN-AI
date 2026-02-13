import { Trash2, Settings, Pencil, Check, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface Session {
    id: string;
    title: string;
    timestamp: string;
}

interface SidebarProps {
    sessions: Session[];
    activeSessionId: string;
    onSessionSelect: (id: string) => void;
    onSessionDelete: (id: string) => void;
    onNewSession: () => void;
    onSettingsClick: () => void;
    onSessionRename?: (id: string, newTitle: string) => void;
}

export const Sidebar = ({
    sessions,
    activeSessionId,
    onSessionSelect,
    onSessionDelete,
    onNewSession,
    onSettingsClick,
    onSessionRename,
}: SidebarProps) => {
    const [hoveredSession, setHoveredSession] = useState<string | null>(null);
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState("");
    const editInputRef = useRef<HTMLInputElement>(null);

    // Focus input when editing starts
    useEffect(() => {
        if (editingSessionId && editInputRef.current) {
            editInputRef.current.focus();
            editInputRef.current.select();
        }
    }, [editingSessionId]);

    const startEditing = (session: Session, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingSessionId(session.id);
        setEditTitle(session.title);
    };

    const saveEdit = () => {
        if (editingSessionId && editTitle.trim() && onSessionRename) {
            onSessionRename(editingSessionId, editTitle.trim());
        }
        setEditingSessionId(null);
        setEditTitle("");
    };

    const cancelEdit = () => {
        setEditingSessionId(null);
        setEditTitle("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            e.preventDefault();
            saveEdit();
        } else if (e.key === "Escape") {
            e.preventDefault();
            cancelEdit();
        }
    };

    return (
        <div className="w-[280px] h-screen bg-black border-r-2 border-primary relative flex flex-col" style={{ boxShadow: "2px 0 20px rgba(0, 217, 255, 0.3)" }}>
            {/* Logo */}
            <div className="p-8 border-b border-primary/30">
                <h1 className="text-3xl font-orbitron font-black text-primary glow-cyan tracking-[0.75rem]">
                    AIZEN
                </h1>
            </div>

            {/* New Session Button */}
            <div className="p-6">
                <button
                    onClick={onNewSession}
                    className="w-full py-3 px-4 border-2 border-primary rounded-lg bg-transparent text-primary font-aldrich tracking-wider text-sm uppercase transition-all duration-300 hover:bg-primary hover:text-black hover:shadow-[0_0_20px_rgba(0,217,255,0.6)]"
                >
                    NEW SESSION
                </button>
            </div>

            {/* Session History */}
            <div className="flex-1 overflow-hidden flex flex-col px-6">
                <h2 className="text-xs font-aldrich tracking-widest text-muted-foreground mb-4 uppercase">
                    SESSION HISTORY
                </h2>

                <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                    {sessions.map((session) => {
                        const isActive = session.id === activeSessionId;
                        const isHovered = hoveredSession === session.id;
                        const isEditing = editingSessionId === session.id;

                        return (
                            <div
                                key={session.id}
                                className={`
                  relative p-4 rounded-lg bg-card border-l-[3px] cursor-pointer
                  transition-all duration-300
                  ${isActive ? "border-primary shadow-[0_0_20px_rgba(0,217,255,0.4)]" : "border-primary/50"}
                  ${isHovered && !isEditing ? "translate-x-2" : ""}
                `}
                                onClick={() => !isEditing && onSessionSelect(session.id)}
                                onMouseEnter={() => setHoveredSession(session.id)}
                                onMouseLeave={() => setHoveredSession(null)}
                                style={{
                                    boxShadow: isActive
                                        ? "0 0 20px rgba(0, 217, 255, 0.4)"
                                        : isHovered
                                            ? "0 0 10px rgba(0, 217, 255, 0.2)"
                                            : "none",
                                }}
                            >
                                {/* Title - editable or display */}
                                {isEditing ? (
                                    <div className="flex items-center gap-2">
                                        <input
                                            ref={editInputRef}
                                            type="text"
                                            value={editTitle}
                                            onChange={(e) => setEditTitle(e.target.value)}
                                            onKeyDown={handleKeyDown}
                                            onBlur={saveEdit}
                                            className="flex-1 text-sm font-electrolize text-foreground bg-black/60 border border-primary/50 rounded px-2 py-1 focus:outline-none focus:border-primary"
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                        <button
                                            onClick={(e) => { e.stopPropagation(); saveEdit(); }}
                                            className="p-1 text-accent hover:text-accent/80 transition-colors"
                                        >
                                            <Check className="w-3 h-3" />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); cancelEdit(); }}
                                            className="p-1 text-destructive hover:text-destructive/80 transition-colors"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    </div>
                                ) : (
                                    <p
                                        className="text-sm font-electrolize text-foreground mb-1 truncate"
                                        onDoubleClick={(e) => startEditing(session, e)}
                                    >
                                        {session.title}
                                    </p>
                                )}

                                <p className="text-xs text-muted-foreground font-quantico">
                                    {session.timestamp}
                                </p>

                                {/* Action buttons on hover */}
                                {isHovered && !isEditing && (
                                    <div className="absolute top-2 right-2 flex gap-1">
                                        {/* Edit button */}
                                        <button
                                            onClick={(e) => startEditing(session, e)}
                                            className="p-1 rounded bg-primary/20 border border-primary/50 text-primary hover:bg-primary/40 transition-all duration-200"
                                        >
                                            <Pencil className="w-3 h-3" />
                                        </button>
                                        {/* Delete button */}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onSessionDelete(session.id);
                                            }}
                                            className="p-1 rounded bg-destructive/20 border border-destructive text-destructive hover:bg-destructive hover:text-white transition-all duration-200"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Settings button at bottom */}
            <div className="p-4 border-t border-primary/30 bg-black/60 backdrop-blur-sm">
                <button
                    onClick={onSettingsClick}
                    className="w-full flex items-center gap-3 p-3 rounded-lg bg-black/60 border-2 border-primary/30 text-primary hover:bg-primary/10 hover:border-primary transition-all duration-300 group"
                >
                    <Settings className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" />
                    <span className="font-aldrich uppercase tracking-wider text-sm">Settings</span>
                </button>
            </div>
        </div>
    );
};
