import React from 'react'
import type { CalendarView } from './CalendarView';

type Props = {
    title: string;
    onPrev: () => void;
    onNext: () => void;
    onToday: () => void;
    view: CalendarView;
};

export const TopBar = (props: Props) => {
  return (
    <div>TopBar</div>
  );
};