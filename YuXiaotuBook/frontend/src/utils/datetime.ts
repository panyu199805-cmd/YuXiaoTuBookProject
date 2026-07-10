/** 将 API 返回的时间格式化为北京时间（UTC+8） */
export function formatBeijingTime(value?: string | null): string {
  if (!value) return '—'

  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const asUtc = /[zZ]|[+-]\d{2}:\d{2}$/.test(normalized) ? normalized : `${normalized}Z`
  const date = new Date(asUtc)
  if (Number.isNaN(date.getTime())) {
    return value.replace('T', ' ').slice(0, 19)
  }

  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)
  const pick = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((p) => p.type === type)?.value ?? ''
  return `${pick('year')}-${pick('month')}-${pick('day')} ${pick('hour')}:${pick('minute')}:${pick('second')}`
}
