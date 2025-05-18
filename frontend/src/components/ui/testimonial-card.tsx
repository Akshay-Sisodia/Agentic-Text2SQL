import React from "react";
import { cn } from "@/lib/utils"
import { Avatar, AvatarImage } from "@/components/ui/avatar"

export interface TestimonialAuthor {
  name: string
  handle: string
  avatar: string
}

export interface TestimonialCardProps {
  author: TestimonialAuthor
  text: string
  href?: string
  className?: string
  date?: string
  rating?: number
  featured?: boolean
}

// Define the types more explicitly
type CardElementProps = 
  | { as: 'a'; href: string; className?: string; children: React.ReactNode }
  | { as: 'div'; className?: string; children: React.ReactNode };

const CardElement: React.FC<CardElementProps> = ({ 
  as: Component, 
  className, 
  children, 
  ...props 
}) => (
  <Component className={className} {...props}>
    {children}
  </Component>
);

export function TestimonialCard({ 
  author,
  text,
  href,
  className
}: TestimonialCardProps) {
  return (
    href ? (
      <CardElement
        as="a"
        href={href}
        className={cn(
          "flex flex-col rounded-lg border-t",
          "bg-gradient-to-b from-muted/50 to-muted/10 dark:from-muted/30 dark:to-muted/5",
          "p-5 text-start sm:p-6",
          "hover:from-muted/70 hover:to-muted/30 dark:hover:from-muted/40 dark:hover:to-muted/20",
          "hover:border-primary/20 hover:shadow-lg",
          "max-w-[320px] sm:max-w-[320px]",
          "transition-all duration-300",
          className
        )}
      >
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 border-2 border-white/10">
            <AvatarImage src={author.avatar} alt={`Profile picture of ${author.name}`} />
            <div aria-hidden="true">{author.name.charAt(0)}</div>
          </Avatar>
          <div className="flex flex-col items-start">
            <h3 className="text-md font-semibold leading-none text-white">
              {author.name}
            </h3>
            <p className="text-sm text-white/60">
              {author.handle}
            </p>
          </div>
        </div>
        <p className="sm:text-md mt-5 text-sm text-white/80 leading-relaxed line-clamp-4 hover:line-clamp-none transition-all duration-300">
          {text}
        </p>
      </CardElement>
    ) : (
      <CardElement
        as="div"
        className={cn(
          "flex flex-col rounded-lg border-t",
          "bg-gradient-to-b from-muted/50 to-muted/10 dark:from-muted/30 dark:to-muted/5",
          "p-5 text-start sm:p-6",
          "hover:from-muted/70 hover:to-muted/30 dark:hover:from-muted/40 dark:hover:to-muted/20",
          "hover:border-primary/20 hover:shadow-lg",
          "max-w-[320px] sm:max-w-[320px]",
          "transition-all duration-300",
          className
        )}
      >
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 border-2 border-white/10">
            <AvatarImage src={author.avatar} alt={`Profile picture of ${author.name}`} />
            <div aria-hidden="true">{author.name.charAt(0)}</div>
          </Avatar>
          <div className="flex flex-col items-start">
            <h3 className="text-md font-semibold leading-none text-white">
              {author.name}
            </h3>
            <p className="text-sm text-white/60">
              {author.handle}
            </p>
          </div>
        </div>
        <p className="sm:text-md mt-5 text-sm text-white/80 leading-relaxed line-clamp-4 hover:line-clamp-none transition-all duration-300">
          {text}
        </p>
      </CardElement>
    )
  )
} 