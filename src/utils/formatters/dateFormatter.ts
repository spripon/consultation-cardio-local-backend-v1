
export const formatDate = (dateString: string) => {
  if (!dateString) return '';
  if (dateString.includes('/')) return dateString;
  const [year, month, day] = dateString.split('-');
  return `${day}/${month}/${year}`;
};
