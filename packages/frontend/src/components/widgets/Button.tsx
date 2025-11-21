import React, { ReactNode } from 'react';
import './Button.css';

type ButtonProps = {
  label?: string;
  icon?: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  iconPosition?: 'left' | 'right';
};

const Button: React.FC<ButtonProps> = ({
  label,
  icon,
  onClick,
  disabled = false,
  className = '',
  iconPosition = 'left',
}) => {
  return (
    <button
      className={`custom-button ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && iconPosition === 'left' && (
        <span className="button-icon">{icon}</span>
      )}
      {label && <span className="button-label">{label}</span>}
      {icon && iconPosition === 'right' && (
        <span className="button-icon">{icon}</span>
      )}
    </button>
  );
};

export default Button;
