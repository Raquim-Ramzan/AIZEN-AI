import { Search, FileText, Code, Calendar, Loader2 } from "lucide-react";

interface ToolExecutionIndicatorProps {
    tool: string;
    status: "running" | "completed" | "error";
}

export const ToolExecutionIndicator = ({ tool, status }: ToolExecutionIndicatorProps) => {
    const getToolIcon = () => {
        switch (tool) {
            case "web_search":
                return <Search className="w-4 h-4" />;
            case "file_ops":
                return <FileText className="w-4 h-4" />;
            case "code_exec":
                return <Code className="w-4 h-4" />;
            case "calendar":
                return <Calendar className="w-4 h-4" />;
            default:
                return <Loader2 className="w-4 h-4 animate-spin" />;
        }
    };

    const getToolName = () => {
        switch (tool) {
            case "web_search":
                return "Web Search";
            case "file_ops":
                return "File Operations";
            case "code_exec":
                return "Code Execution";
            case "calendar":
                return "Calendar";
            default:
                return "Tool";
        }
    };

    const getStatusColor = () => {
        switch (status) {
            case "running":
                return "text-primary border-primary/50 bg-primary/5";
            case "completed":
                return "text-accent border-accent/50 bg-accent/5";
            case "error":
                return "text-destructive border-destructive/50 bg-destructive/5";
        }
    };

    const getStatusText = () => {
        switch (status) {
            case "running":
                return "EXECUTING";
            case "completed":
                return "COMPLETED";
            case "error":
                return "ERROR";
        }
    };

    return (
        <div
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border-2 ${getStatusColor()} font-quantico text-xs transition-all duration-300`}
        >
            <div className={status === "running" ? "animate-pulse" : ""}>
                {getToolIcon()}
            </div>
            <div className="flex flex-col">
                <span className="font-bold uppercase tracking-wide">{getToolName()}</span>
                <span className="text-[10px] opacity-70">{getStatusText()}</span>
            </div>
            {status === "running" && (
                <div className="flex gap-1">
                    <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                    <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                    <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
                </div>
            )}
        </div>
    );
};
