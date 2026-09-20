export const formatApiDate = (dateObj: any): string => {
  if (!dateObj) return '—';

  try {
    // Check for Java LocalDateTime array: [year, month, day, hour, minute, second, nano]
    if (Array.isArray(dateObj) && dateObj.length >= 3) {
      // month is 1-indexed in the array, but JS Date uses 0-indexed month
      const [year, month, day, hour = 0, minute = 0, second = 0] = dateObj;
      const d = new Date(year, month - 1, day, hour, minute, second);
      return isNaN(d.getTime()) ? 'Invalid Date' : d.toLocaleDateString();
    }
    
    if (typeof dateObj === 'string' || typeof dateObj === 'number') {
      const d = new Date(dateObj);
      return isNaN(d.getTime()) ? 'Invalid Date' : d.toLocaleDateString();
    }
    
    return '—';
  } catch {
    return 'Invalid Date';
  }
};
