import { useState, useEffect } from "react";
import { X, Database, Plus, Trash2, Edit3, Save, AlertTriangle, Brain, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { memoryService, CoreFact } from "@/services/memory.service";
import { toast } from "sonner";

interface CoreMemoryEditorProps {
    isOpen: boolean;
    onClose: () => void;
}

export const CoreMemoryEditor = ({ isOpen, onClose }: CoreMemoryEditorProps) => {
    const [facts, setFacts] = useState<CoreFact[]>([]);
    const [loading, setLoading] = useState(true);
    const [newFact, setNewFact] = useState("");
    const [newCategory, setNewCategory] = useState("learned");
    const [newImportance, setNewImportance] = useState("normal");
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editingText, setEditingText] = useState("");
    const [showClearConfirm, setShowClearConfirm] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        if (isOpen) {
            loadFacts();
        }
    }, [isOpen]);

    const loadFacts = async () => {
        setLoading(true);
        try {
            const response = await memoryService.getCoreFacts();
            if (response.data) {
                setFacts(response.data.facts || []);
            }
        } catch (error) {
            console.error('[CoreMemoryEditor] Error loading facts:', error);
            toast.error("Failed to load core memory");
        } finally {
            setLoading(false);
        }
    };

    const handleAddFact = async () => {
        if (!newFact.trim()) {
            toast.error("Please enter a fact");
            return;
        }

        try {
            const response = await memoryService.addCoreFact(
                newFact.trim(),
                newCategory,
                newImportance
            );

            if (response.data?.status === "created") {
                toast.success("Memory added successfully");
                setNewFact("");
                loadFacts();
            } else if (response.data?.status === "duplicate") {
                toast.warning("This memory already exists");
            } else {
                toast.error("Failed to add memory");
            }
        } catch (error) {
            console.error('[CoreMemoryEditor] Error adding fact:', error);
            toast.error("Failed to add memory");
        }
    };

    const handleEditFact = (fact: CoreFact) => {
        if (!fact.id) return;
        setEditingId(fact.id);
        setEditingText(fact.fact);
    };

    const handleSaveEdit = async (factId: string) => {
        if (!editingText.trim()) {
            toast.error("Memory cannot be empty");
            return;
        }

        try {
            const response = await memoryService.updateCoreFact(factId, editingText.trim());
            if (response.data?.status === "updated") {
                toast.success("Memory updated");
                setEditingId(null);
                setEditingText("");
                loadFacts();
            } else {
                toast.error("Failed to update memory");
            }
        } catch (error) {
            console.error('[CoreMemoryEditor] Error updating fact:', error);
            toast.error("Failed to update memory");
        }
    };

    const handleDeleteFact = async (factId: string) => {
        try {
            const response = await memoryService.deleteCoreFact(factId);
            if (response.data?.status === "deleted") {
                toast.success("Memory deleted");
                loadFacts();
            } else {
                toast.error("Failed to delete memory");
            }
        } catch (error) {
            console.error('[CoreMemoryEditor] Error deleting fact:', error);
            toast.error("Failed to delete memory");
        }
    };

    const handleClearAll = async (keepIdentity: boolean) => {
        try {
            const response = await memoryService.clearCoreFacts(keepIdentity);
            if (response.data?.status === "cleared") {
                toast.success(keepIdentity ? "Learned memories cleared" : "All memories cleared");
                setShowClearConfirm(false);
                loadFacts();
            } else {
                toast.error("Failed to clear memories");
            }
        } catch (error) {
            console.error('[CoreMemoryEditor] Error clearing facts:', error);
            toast.error("Failed to clear memories");
        }
    };

    const filteredFacts = facts.filter(fact =>
        fact.fact.toLowerCase().includes(searchQuery.toLowerCase()) ||
        fact.category?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getCategoryColor = (category: string) => {
        switch (category) {
            case "identity": return "bg-purple-500/20 text-purple-400 border-purple-500/30";
            case "preference": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
            case "user_info": return "bg-green-500/20 text-green-400 border-green-500/30";
            case "learned": return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
            default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
        }
    };

    const getImportanceColor = (importance: string) => {
        switch (importance) {
            case "critical": return "text-red-400";
            case "high": return "text-orange-400";
            default: return "text-gray-400";
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Panel */}
            <div className="relative w-full max-w-4xl mx-4 bg-black border-2 border-primary/30 rounded-lg shadow-[0_0_40px_rgba(0,217,255,0.3)] animate-scale-in max-h-[85vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-primary/30">
                    <div className="flex items-center gap-3">
                        <Brain className="w-6 h-6 text-primary glow-cyan" />
                        <h2 className="text-2xl font-orbitron font-bold text-primary glow-cyan tracking-wider">
                            CORE MEMORY
                        </h2>
                        <Badge variant="outline" className="ml-2 text-accent">
                            {facts.length} memories
                        </Badge>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onClose}
                        className="text-primary hover:bg-primary/10"
                    >
                        <X className="w-5 h-5" />
                    </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden flex flex-col">
                    {/* Add New Memory Section */}
                    <div className="p-4 border-b border-primary/20 bg-black/40">
                        <div className="flex items-center gap-2 mb-3">
                            <Plus className="w-4 h-4 text-accent" />
                            <Label className="text-sm font-aldrich text-primary uppercase tracking-wide">
                                Add New Memory
                            </Label>
                        </div>
                        <div className="flex gap-2">
                            <Input
                                value={newFact}
                                onChange={(e) => setNewFact(e.target.value)}
                                placeholder="Enter a fact or knowledge to remember..."
                                className="flex-1 bg-black/60 border-primary/30 focus:border-primary text-foreground"
                                onKeyDown={(e) => e.key === "Enter" && handleAddFact()}
                            />
                            <select
                                value={newCategory}
                                onChange={(e) => setNewCategory(e.target.value)}
                                className="px-3 py-2 bg-black/60 border border-primary/30 rounded-md text-foreground text-sm"
                            >
                                <option value="learned">Learned</option>
                                <option value="preference">Preference</option>
                                <option value="user_info">User Info</option>
                                <option value="identity">Identity</option>
                            </select>
                            <select
                                value={newImportance}
                                onChange={(e) => setNewImportance(e.target.value)}
                                className="px-3 py-2 bg-black/60 border border-primary/30 rounded-md text-foreground text-sm"
                            >
                                <option value="normal">Normal</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                            <Button
                                onClick={handleAddFact}
                                className="bg-accent/20 border border-accent/30 text-accent hover:bg-accent/30"
                            >
                                <Plus className="w-4 h-4 mr-1" />
                                Add
                            </Button>
                        </div>
                    </div>

                    {/* Search */}
                    <div className="p-4 border-b border-primary/20">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search memories..."
                                className="pl-10 bg-black/60 border-primary/30 focus:border-primary text-foreground"
                            />
                        </div>
                    </div>

                    {/* Memory List */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-2">
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full" />
                            </div>
                        ) : filteredFacts.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p className="font-quantico">No memories found</p>
                            </div>
                        ) : (
                            filteredFacts.map((fact) => (
                                <div
                                    key={fact.id || fact.fact}
                                    className="p-3 bg-black/40 border border-primary/20 rounded-lg hover:border-primary/40 transition-colors group"
                                >
                                    {editingId === fact.id ? (
                                        <div className="flex items-center gap-2">
                                            <Input
                                                value={editingText}
                                                onChange={(e) => setEditingText(e.target.value)}
                                                className="flex-1 bg-black/60 border-primary/30 text-foreground"
                                                onKeyDown={(e) => e.key === "Enter" && handleSaveEdit(fact.id!)}
                                            />
                                            <Button
                                                size="sm"
                                                onClick={() => handleSaveEdit(fact.id!)}
                                                className="bg-accent/20 border border-accent/30 text-accent"
                                            >
                                                <Save className="w-4 h-4" />
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                onClick={() => {
                                                    setEditingId(null);
                                                    setEditingText("");
                                                }}
                                                className="text-muted-foreground"
                                            >
                                                <X className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    ) : (
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <p className="text-sm font-electrolize text-foreground mb-2">
                                                    {fact.fact}
                                                </p>
                                                <div className="flex items-center gap-2 text-xs">
                                                    <Badge
                                                        variant="outline"
                                                        className={getCategoryColor(fact.category || "learned")}
                                                    >
                                                        {fact.category || "learned"}
                                                    </Badge>
                                                    {fact.importance && fact.importance !== "normal" && (
                                                        <span className={`font-quantico ${getImportanceColor(fact.importance)}`}>
                                                            {fact.importance}
                                                        </span>
                                                    )}
                                                    {fact.source && (
                                                        <span className="text-muted-foreground font-quantico">
                                                            via {fact.source}
                                                        </span>
                                                    )}
                                                    {fact.timestamp && (
                                                        <span className="text-muted-foreground font-quantico">
                                                            {new Date(fact.timestamp).toLocaleDateString()}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                {fact.source !== "system" && (
                                                    <>
                                                        <Button
                                                            size="icon"
                                                            variant="ghost"
                                                            onClick={() => handleEditFact(fact)}
                                                            className="h-8 w-8 text-primary hover:bg-primary/20"
                                                        >
                                                            <Edit3 className="w-4 h-4" />
                                                        </Button>
                                                        <Button
                                                            size="icon"
                                                            variant="ghost"
                                                            onClick={() => handleDeleteFact(fact.id!)}
                                                            className="h-8 w-8 text-destructive hover:bg-destructive/20"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </Button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-4 border-t border-primary/30 bg-black/60">
                    <div className="flex items-center gap-2">
                        {showClearConfirm ? (
                            <>
                                <span className="text-sm text-destructive font-quantico flex items-center gap-1">
                                    <AlertTriangle className="w-4 h-4" />
                                    Clear all memories?
                                </span>
                                <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => handleClearAll(false)}
                                    className="text-xs"
                                >
                                    Clear All
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleClearAll(true)}
                                    className="text-xs border-yellow-500/30 text-yellow-400"
                                >
                                    Keep Identity
                                </Button>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => setShowClearConfirm(false)}
                                    className="text-xs"
                                >
                                    Cancel
                                </Button>
                            </>
                        ) : (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowClearConfirm(true)}
                                className="text-destructive border-destructive/30 hover:bg-destructive/10"
                            >
                                <Trash2 className="w-4 h-4 mr-1" />
                                Clear Memory
                            </Button>
                        )}
                    </div>
                    <Button
                        onClick={onClose}
                        className="bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 font-aldrich uppercase tracking-wider"
                    >
                        Close
                    </Button>
                </div>
            </div>
        </div>
    );
};
