export const TypingIndicator = () => {
    return (
        <div className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-accent/5 border-2 border-accent/30 w-fit animate-fade-in">
            <div className="flex gap-1.5">
                <div
                    className="w-2 h-2 rounded-full bg-accent animate-bounce"
                    style={{ animationDelay: "0s" }}
                />
                <div
                    className="w-2 h-2 rounded-full bg-accent animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                />
                <div
                    className="w-2 h-2 rounded-full bg-accent animate-bounce"
                    style={{ animationDelay: "0.4s" }}
                />
            </div>
            <span className="text-xs font-quantico text-accent uppercase tracking-wider">
                AI is thinking...
            </span>
        </div>
    );
};
