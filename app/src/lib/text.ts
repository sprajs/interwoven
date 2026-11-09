/** Turn a vocabulary id into words: `first_known` becomes "First known". */
export function words(id: string): string {
  const text = id.replace(/[_-]/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function plural(count: number, one: string, many = `${one}s`): string {
  return `${count.toLocaleString('en-GB').replace(/,/g, ' ')} ${count === 1 ? one : many}`
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

/** A date label as a reader would write it: "1956-06" becomes "June 1956". Other labels pass through. */
export function dateLabel(label: string): string {
  const iso = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(label)
  if (!iso) return label
  const month = MONTHS[Number(iso[2]) - 1] ?? ''
  return iso[3] ? `${Number(iso[3])} ${month} ${iso[1]}` : `${month} ${iso[1]}`
}

/** A date label trimmed for tight places: the note in brackets goes, and "Approximately" becomes "c." */
export function shortDate(label: string): string {
  return dateLabel(label)
    .replace(/\s*\(.*$/, '')
    .replace(/\b[Aa]pproximately\s+/, 'c. ')
    .replace(/\b[Aa]bout\s+/, 'c. ')
    .replace(/^By c\./, 'By c.')
}
