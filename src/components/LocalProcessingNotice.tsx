import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Mention discrète rappelant que tout le traitement est local.
 */
export const LocalProcessingNotice = ({ className }: { className?: string }) => (
  <p
    className={cn(
      "flex items-center gap-1.5 text-xs text-muted-foreground",
      className,
    )}
  >
    <ShieldCheck className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
    <span>Traitement local — aucune donnée envoyée vers un service IA externe</span>
  </p>
);