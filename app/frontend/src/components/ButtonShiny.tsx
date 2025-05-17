import React from 'react';
import { Button } from "./ui/button";
import { cn } from "../lib/utils";
import type { ReactNode } from 'react';

export interface ButtonShinyProps {
  label: string;
  onClick?: () => void;
  endIcon?: ReactNode;
  startIcon?: ReactNode;
  className?: string;
  sx?: React.CSSProperties;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

const ButtonShiny: React.FC<ButtonShinyProps> = ({
  label,
  onClick,
  endIcon,
  startIcon,
  className,
  sx = {},
  disabled = false,
  type = 'button'
}) => {
  return (
    <Button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "group relative overflow-hidden bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/30",
        className
      )}
      style={sx}
    >
      <span className="buttonContent relative z-10 flex items-center">
        {startIcon && <span className="icon transition-transform duration-300 ease-in-out mr-2">{startIcon}</span>}
        <span className="label bg-gradient-to-r from-slate-50 to-blue-50 bg-clip-text text-transparent">
          {label}
        </span>
        {endIcon && <span className="icon transition-transform duration-300 ease-in-out ml-2 group-hover:translate-x-0.5">{endIcon}</span>}
      </span>
      <span
        className="shine absolute top-[-50%] left-[-100%] w-10 h-[200%] bg-white/20 rotate-30 transition-all duration-700 ease-in-out z-[1] group-hover:left-[125%]"
      />
      <span className="absolute inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-indigo-500 bg-[length:400%_400%] opacity-70 -z-10 rounded-md animate-gradient-shift"></span>
    </Button>
  );
};

export default ButtonShiny; 