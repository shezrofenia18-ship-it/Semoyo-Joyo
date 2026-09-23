import { Button } from "@/components/ui/button";

export const EmptyState = ({ icon: Icon, title, description, actionLabel, onAction, testId }) => (
  <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed bg-card px-6 py-14 text-center" data-testid={testId}>
    {Icon && (
      <span className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Icon className="h-6 w-6" />
      </span>
    )}
    <p className="font-display text-lg font-semibold">{title}</p>
    {description && <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>}
    {actionLabel && (
      <Button className="mt-5" onClick={onAction}>
        {actionLabel}
      </Button>
    )}
  </div>
);
