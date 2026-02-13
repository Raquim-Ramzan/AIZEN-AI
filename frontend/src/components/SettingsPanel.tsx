import { useState, useEffect } from "react";
import { X, Settings, Cpu, Mic, Volume2, Database, CheckCircle2, XCircle, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ModelSelector } from "./ModelSelector";
import { Badge } from "@/components/ui/badge";
import { systemService } from "@/services/system.service";
import { CoreMemoryEditor } from "./CoreMemoryEditor";
import type { Settings as SettingsType } from "@/types/api.types";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onModelChange?: (provider?: string, model?: string) => void;
  autoSpeak?: boolean;
  onAutoSpeakChange?: (enabled: boolean) => void;
}

export const SettingsPanel = ({ isOpen, onClose, onModelChange, autoSpeak: autoSpeakProp, onAutoSpeakChange }: SettingsPanelProps) => {
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>("auto");
  const [selectedModel, setSelectedModel] = useState<string>("auto");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [autoSpeak, setAutoSpeak] = useState(autoSpeakProp ?? false);
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [coreMemoryEditorOpen, setCoreMemoryEditorOpen] = useState(false);

  // Sync autoSpeak with prop
  useEffect(() => {
    if (autoSpeakProp !== undefined) {
      setAutoSpeak(autoSpeakProp);
    }
  }, [autoSpeakProp]);

  // Handle autoSpeak toggle
  const handleAutoSpeakChange = (enabled: boolean) => {
    setAutoSpeak(enabled);
    onAutoSpeakChange?.(enabled);
    // Persist to localStorage
    localStorage.setItem('aizen-autospeak', JSON.stringify(enabled));
  };

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      const response = await systemService.getSettings();
      if (response.data) {
        setSettings(response.data);
      }
    } catch (error) {
      console.error('[SettingsPanel] Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    if (provider === "auto") {
      setSelectedModel("auto");
      onModelChange?.();
    } else {
      onModelChange?.(provider, selectedModel !== "auto" ? selectedModel : undefined);
    }
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    onModelChange?.(
      selectedProvider !== "auto" ? selectedProvider : undefined,
      model !== "auto" ? model : undefined
    );
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
      <div className="relative w-full max-w-3xl mx-4 bg-black border-2 border-primary/30 rounded-lg shadow-[0_0_40px_rgba(0,217,255,0.3)] animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-primary/30">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-primary glow-cyan" />
            <h2 className="text-2xl font-orbitron font-bold text-primary glow-cyan tracking-wider">
              SYSTEM SETTINGS
            </h2>
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
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto scrollbar-custom">
          {/* Provider Status */}
          {settings && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary" />
                <h3 className="text-lg font-aldrich text-primary uppercase tracking-wide">
                  AI Providers Status
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-3 pl-7">
                {Object.entries(settings.providers).map(([provider, info]) => (
                  <div
                    key={provider}
                    className="flex items-center justify-between p-3 bg-background/30 border border-primary/20 rounded-lg"
                  >
                    <span className="text-sm font-quantico capitalize">{provider}</span>
                    {info.configured ? (
                      <Badge variant="outline" className="text-accent flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Ready
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground flex items-center gap-1">
                        <XCircle className="w-3 h-3" />
                        Not Configured
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Model Selection */}
          <div className="space-y-4 pt-4 border-t border-primary/20">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-aldrich text-primary uppercase tracking-wide">
                AI Model Selection
              </h3>
            </div>
            <div className="pl-7">
              <ModelSelector
                selectedProvider={selectedProvider}
                selectedModel={selectedModel}
                onProviderChange={handleProviderChange}
                onModelChange={handleModelChange}
              />
            </div>
          </div>

          {/* Model Preferences */}
          {settings && (
            <div className="space-y-4 pt-4 border-t border-primary/20">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-accent" />
                <h3 className="text-lg font-aldrich text-primary uppercase tracking-wide">
                  Task Preferences
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-2 pl-7 text-xs font-quantico">
                <div className="flex justify-between items-center p-2 bg-background/20 rounded">
                  <span className="text-muted-foreground">Coding:</span>
                  <span className="text-accent">{settings.model_preferences.coding}</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-background/20 rounded">
                  <span className="text-muted-foreground">Chat:</span>
                  <span className="text-accent">{settings.model_preferences.chat}</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-background/20 rounded">
                  <span className="text-muted-foreground">Reasoning:</span>
                  <span className="text-accent">{settings.model_preferences.reasoning}</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-background/20 rounded">
                  <span className="text-muted-foreground">Search:</span>
                  <span className="text-accent">{settings.model_preferences.search}</span>
                </div>
              </div>
            </div>
          )}

          {/* Voice Settings */}
          <div className="space-y-4 pt-4 border-t border-primary/20">
            <div className="flex items-center gap-2">
              <Mic className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-aldrich text-primary uppercase tracking-wide">
                Voice Input
              </h3>
            </div>
            <div className="space-y-4 pl-7">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="voice" className="text-sm font-electrolize text-foreground">
                    Enable Voice Input
                  </Label>
                  <p className="text-xs text-muted-foreground font-quantico">
                    Use Alt + PgUp to activate voice mode
                  </p>
                </div>
                <Switch
                  id="voice"
                  checked={voiceEnabled}
                  onCheckedChange={setVoiceEnabled}
                  className="data-[state=checked]:bg-accent"
                />
              </div>
            </div>
          </div>

          {/* Voice Output Settings */}
          <div className="space-y-4 pt-4 border-t border-primary/20">
            <div className="flex items-center gap-2">
              <Volume2 className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-aldrich text-primary uppercase tracking-wide">
                Voice Output
              </h3>
            </div>
            <div className="space-y-4 pl-7">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="autospeak" className="text-sm font-electrolize text-foreground">
                    Auto-Speak Responses
                  </Label>
                  <p className="text-xs text-muted-foreground font-quantico">
                    Automatically read AI responses aloud
                  </p>
                </div>
                <Switch
                  id="autospeak"
                  checked={autoSpeak}
                  onCheckedChange={handleAutoSpeakChange}
                  className="data-[state=checked]:bg-accent"
                />
              </div>
            </div>
          </div>

          {/* Memory Settings */}
          <div className="space-y-4 pt-4 border-t border-primary/20">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-aldrich text-primary uppercase tracking-wide">
                Memory System
              </h3>
            </div>
            <div className="space-y-4 pl-7">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="memory" className="text-sm font-electrolize text-foreground">
                    Core Memory
                  </Label>
                  <p className="text-xs text-muted-foreground font-quantico">
                    Remember user preferences and learned facts
                  </p>
                </div>
                <Switch
                  id="memory"
                  checked={memoryEnabled}
                  onCheckedChange={setMemoryEnabled}
                  className="data-[state=checked]:bg-primary"
                />
              </div>
              {/* Core Memory Editor Button */}
              <Button
                onClick={() => setCoreMemoryEditorOpen(true)}
                variant="outline"
                className="w-full justify-start gap-2 bg-black/40 border-primary/30 hover:bg-primary/10 hover:border-primary/60"
              >
                <Brain className="w-4 h-4 text-primary" />
                <span className="font-quantico">Edit Core Memory</span>
              </Button>
            </div>
          </div>

          {/* Core Memory Editor Modal */}
          <CoreMemoryEditor
            isOpen={coreMemoryEditorOpen}
            onClose={() => setCoreMemoryEditorOpen(false)}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-primary/30">
          <p className="text-xs text-muted-foreground font-quantico">
            Settings are saved automatically
          </p>
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
