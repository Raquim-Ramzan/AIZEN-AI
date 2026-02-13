/**
 * Model Selector Component
 * Allows users to manually select AI provider and model
 */

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { systemService } from '@/services/system.service';
import type { AvailableModels } from '@/types/api.types';
import { Loader2, Sparkles, Zap, Search, Brain } from 'lucide-react';

interface ModelSelectorProps {
    selectedProvider?: string;
    selectedModel?: string;
    onProviderChange?: (provider: string) => void;
    onModelChange?: (model: string) => void;
}

export const ModelSelector = ({
    selectedProvider,
    selectedModel,
    onProviderChange,
    onModelChange,
}: ModelSelectorProps) => {
    const [models, setModels] = useState<AvailableModels | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadModels();
    }, []);

    const loadModels = async () => {
        try {
            const response = await systemService.getAvailableModels();
            if (response.data) {
                setModels(response.data);
            }
        } catch (error) {
            console.error('[ModelSelector] Error loading models:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Card className="p-4 bg-background/50 backdrop-blur-md border-primary/20">
                <div className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm font-quantico">Loading models...</span>
                </div>
            </Card>
        );
    }

    if (!models) {
        return null;
    }

    const getProviderIcon = (provider: string) => {
        switch (provider) {
            case 'gemini':
                return <Sparkles className="w-4 h-4" />;
            case 'groq':
                return <Zap className="w-4 h-4" />;
            case 'perplexity':
                return <Search className="w-4 h-4" />;
            case 'ollama':
                return <Brain className="w-4 h-4" />;
            default:
                return null;
        }
    };

    const getProviderColor = (provider: string) => {
        switch (provider) {
            case 'gemini':
                return 'text-blue-400';
            case 'groq':
                return 'text-purple-400';
            case 'perplexity':
                return 'text-green-400';
            case 'ollama':
                return 'text-orange-400';
            default:
                return 'text-gray-400';
        }
    };

    const availableProviders = Object.entries(models).filter(
        ([_, info]) => info.available
    );

    return (
        <Card className="p-4 bg-background/50 backdrop-blur-md border-primary/20">
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-quantico text-foreground">AI Provider</h3>
                    {selectedProvider && (
                        <Badge variant="outline" className="text-accent">
                            {selectedProvider}
                        </Badge>
                    )}
                </div>

                {/* Provider Selection */}
                <Select value={selectedProvider} onValueChange={onProviderChange}>
                    <SelectTrigger className="w-full bg-background/30 border-primary/30">
                        <SelectValue placeholder="Auto-select (Recommended)" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="auto">
                            <span className="flex items-center gap-2">
                                <Sparkles className="w-3 h-3" />
                                Auto-select (Recommended)
                            </span>
                        </SelectItem>
                        {availableProviders.map(([provider, info]) => (
                            <SelectItem key={provider} value={provider}>
                                <span className={`flex items-center gap-2 ${getProviderColor(provider)}`}>
                                    {getProviderIcon(provider)}
                                    {provider.toUpperCase()}
                                    {info.models.length > 0 && (
                                        <span className="text-xs text-muted-foreground">
                                            ({info.models.length} models)
                                        </span>
                                    )}
                                </span>
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>

                {/* Model Selection */}
                {selectedProvider && selectedProvider !== 'auto' && (
                    <div className="space-y-2">
                        <h4 className="text-xs font-quantico text-muted-foreground">
                            Select Model
                        </h4>
                        <Select value={selectedModel} onValueChange={onModelChange}>
                            <SelectTrigger className="w-full bg-background/30 border-primary/30">
                                <SelectValue placeholder="Default for task" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="auto">Default for task</SelectItem>
                                {models[selectedProvider as keyof AvailableModels]?.models.map(
                                    (model) => (
                                        <SelectItem key={model.name} value={model.name}>
                                            <div className="flex flex-col gap-1">
                                                <span className="text-sm">{model.name}</span>
                                                <span className="text-xs text-muted-foreground">
                                                    {model.description}
                                                </span>
                                            </div>
                                        </SelectItem>
                                    )
                                )}
                            </SelectContent>
                        </Select>
                    </div>
                )}

                {/* Reset Button */}
                {selectedProvider && selectedProvider !== 'auto' && (
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                            onProviderChange?.('auto');
                            onModelChange?.('auto');
                        }}
                        className="w-full text-xs"
                    >
                        Reset to Auto
                    </Button>
                )}

                {/* Info */}
                <p className="text-[10px] text-muted-foreground font-quantico text-center">
                    Auto-select uses the best model for each task type
                </p>
            </div>
        </Card>
    );
};
