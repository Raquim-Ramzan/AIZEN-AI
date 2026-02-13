import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, Info } from "lucide-react";
import { toast } from "sonner";
import type { PendingOperation, OperationParameters } from "@/types/api.types";

interface SystemOperationApprovalProps {
  operation: PendingOperation | null;
  onApprove: (operationId: string, remember: boolean) => Promise<void>;
  onDeny: (operationId: string) => Promise<void>;
  onClose: () => void;
}

const RISK_COLORS = {
  safe: "bg-green-500/20 text-green-300 border-green-500/30",
  needs_approval: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  dangerous: "bg-red-500/20 text-red-300 border-red-500/30",
};

const RISK_ICONS = {
  safe: CheckCircle,
  needs_approval: Info,
  dangerous: AlertTriangle,
};

export function SystemOperationApproval({
  operation,
  onApprove,
  onDeny,
  onClose,
}: SystemOperationApprovalProps) {
  const [loading, setLoading] = useState(false);
  const [remember, setRemember] = useState(false);

  if (!operation) return null;

  const riskLevel = (operation.risk_level || "needs_approval") as keyof typeof RISK_COLORS;
  const RiskIcon = RISK_ICONS[riskLevel];

  const handleApprove = async () => {
    setLoading(true);
    try {
      await onApprove(operation.operation_id, remember);
      toast.success("Operation approved", {
        description: `${operation.tool} is now executing`,
      });
      onClose();
    } catch (error) {
      toast.error("Failed to approve operation");
    } finally {
      setLoading(false);
    }
  };

  const handleDeny = async () => {
    setLoading(true);
    try {
      await onDeny(operation.operation_id);
      toast.info("Operation denied");
      onClose();
    } catch (error) {
      toast.error("Failed to deny operation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={!!operation} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px] bg-black/95 border-primary/20">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <RiskIcon className={`w-6 h-6 ${RISK_COLORS[riskLevel]}`} />
            <DialogTitle className="text-xl font-bold text-primary">
              System Operation Approval
            </DialogTitle>
          </div>
          <DialogDescription className="text-gray-300">
            {operation.message || "The AI wants to perform a system operation."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Operation Details */}
          <div className="bg-primary/5 border border-primary/10 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-400">Operation</span>
              <Badge variant="outline" className="font-mono">
                {operation.tool}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-400">Risk Level</span>
              <Badge
                variant="outline"
                className={`${RISK_COLORS[riskLevel]} border`}
              >
                {riskLevel.replace("_", " ").toUpperCase()}
              </Badge>
            </div>

            {/* Parameters */}
            {Object.keys(operation.parameters).length > 0 && (
              <div className="space-y-2">
                <span className="text-sm font-medium text-gray-400">Parameters:</span>
                <div className="bg-black/40 rounded p-3 space-y-1">
                  {Object.entries(operation.parameters).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-2 text-sm">
                      <span className="text-primary font-medium">{key}:</span>
                      <span className="text-gray-300 font-mono break-all">
                        {typeof value === "object"
                          ? JSON.stringify(value)
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Warning for dangerous operations */}
          {riskLevel === "dangerous" && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-300">
                <p className="font-semibold">Dangerous Operation</p>
                <p className="text-red-400/80">
                  This operation can affect system stability or data integrity. Please review carefully.
                </p>
              </div>
            </div>
          )}

          {/* Remember choice */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="w-4 h-4 rounded border-primary/30 bg-black/40 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-300">
              Remember my choice for this operation type
            </span>
          </label>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleDeny}
            disabled={loading}
            className="border-gray-600 hover:bg-gray-800"
          >
            ❌ Deny
          </Button>
          <Button
            onClick={handleApprove}
            disabled={loading}
            className="bg-gradient-to-r from-primary to-accent hover:opacity-90"
          >
            {loading ? "⏳ Approving..." : "✅ Approve"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
