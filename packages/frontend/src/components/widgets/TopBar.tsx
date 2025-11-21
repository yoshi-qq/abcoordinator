import React from 'react'
import type { CalendarViewType } from './CalendarView';

type Props = {
    title: string;
    onPrev: () => void;
    onNext: () => void;
    onToday: () => void;
    view: CalendarViewType;
};

export const TopBar: React.FC<Props>  = (props: Props) => {
  return (
    <div className='top-bar'>
        <div className='title'>
        </div>
    </div>
  );
};