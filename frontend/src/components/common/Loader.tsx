import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface LoaderProps {
  className?: string;
  size?: number;
}

export function Loader({ className, size = 24 }: LoaderProps) {
  return (
    <Loader2 
      className={cn("animate-spin text-brand-600", className)} 
      size={size} 
    />
  );
}

export function PageLoader() {
  return (
    <div className="flex h-full w-full items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-4">
        <Loader size={32} />
        <p className="text-sm text-slate-500">Loading data...</p>
      </div>
    </div>
  );
}
