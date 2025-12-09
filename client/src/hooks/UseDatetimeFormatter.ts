const timeFormatter = new Intl.DateTimeFormat('en-US', {
  hour: 'numeric',
  minute: 'numeric',
  hour12: true,
});

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

export function useDatetimeFormatter() {
  return (datetime: string | Date) => {
    const dateObj =
      typeof datetime === 'string' ? new Date(datetime) : datetime;

    return {
      date: dateFormatter.format(dateObj),
      time: timeFormatter.format(dateObj),
    };
  };
}
