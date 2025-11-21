import React from "react";

interface Event {
  id: number;
  title: string;
  day: number; // 0 = Monday, 6 = Sunday
  startHour: number; // 0-23
  endHour: number; // 1-24
  color?: string;
}

type CalendarView = "day" | "week" | "month";

interface Props {
  events?: Event[];
}

export const CalendarView: React.FC<Props> = ({ events = [] }) => {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className="week-calendar">
      <div className="header">
        <div className="time-column"></div>
        {days.map((d) => (
          <div key={d} className="day-column-header">
            {d}
          </div>
        ))}
      </div>

      <div className="body">
        {hours.map((hour) => (
          <div key={hour} className="hour-row">
            <div className="time-label">{hour.toString().padStart(2, "0")}:00</div>
            {days.map((_, dayIndex) => {
              const hourEvents = events.filter(
                (e) => e.day === dayIndex && e.startHour <= hour && e.endHour > hour
              );
              return (
                <div key={dayIndex} className="day-cell">
                  {hourEvents.map((e) => (
                    <div
                      key={e.id}
                      className="event"
                      style={{ backgroundColor: e.color || "#90cdf4" }}
                    >
                      {e.title}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};