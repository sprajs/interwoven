/** Turn a vocabulary id into words: `first_known` becomes "First known". */
export function words(id: string): string {
  const text = id.replace(/[_-]/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function plural(count: number, one: string, many = `${one}s`): string {
  return `${count.toLocaleString('en-GB').replace(/,/g, ' ')} ${count === 1 ? one : many}`
}

/** A date label trimmed for tight places: the note in brackets goes, and "Approximately" becomes "c." */
export function shortDate(label: string): string {
  return label.replace(/\s*\(.*$/, '').replace(/^Approximately\s+/i, 'c. ').replace(/^About\s+/i, 'c. ')
}
