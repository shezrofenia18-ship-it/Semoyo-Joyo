import { useState } from "react";
import { Package } from "lucide-react";
import { resolveImage } from "@/lib/api";
import { cn } from "@/lib/utils";

export const ProductImage = ({ src, alt, className, iconClassName = "h-8 w-8", testId }) => {
  const [failed, setFailed] = useState(false);
  const url = resolveImage(src);
  if (!url || failed) {
    return (
      <div className={cn("flex items-center justify-center bg-muted text-muted-foreground", className)} data-testid={testId}>
        <Package className={iconClassName} />
      </div>
    );
  }
  return (
    <img
      src={url}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      className={cn("h-full w-full object-cover", className)}
      data-testid={testId}
    />
  );
};
