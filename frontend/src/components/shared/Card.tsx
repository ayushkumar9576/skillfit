import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export default function Card({ children, className, ...props }: CardProps) {
  return (
    <div 
      className={cn("rounded-2xl border border-slate-200 bg-white shadow-sm", className)} 
      {...props}
    >
      {children}
    </div>
  );
}
