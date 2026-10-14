// Timestamps (§1): `YYYY-MM-DDThh:mm:ssZ`, UTC, whole seconds; the instant is the count of seconds since
// 1970-01-01T00:00:00Z in the proleptic Gregorian calendar, when the date and time exist.

const FORM = /^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})Z$/;

function leap(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
}

const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

/** Days from 1970-01-01 to the given civil date (proleptic Gregorian). */
function daysFromCivil(y: number, m: number, d: number): number {
  const yy = m <= 2 ? y - 1 : y;
  const era = Math.floor(yy / 400);
  const yoe = yy - era * 400;
  const mp = (m + 9) % 12;
  const doy = Math.floor((153 * mp + 2) / 5) + d - 1;
  const doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
  return era * 146097 + doe - 719468;
}

/** The instant of a timestamp, or null when the string names no time. */
export function instant(s: string): number | null {
  const m = FORM.exec(s);
  if (!m) return null;
  const [y, mo, d, h, mi, se] = m.slice(1).map((x) => parseInt(x, 10));
  if (mo < 1 || mo > 12) return null;
  const dim = mo === 2 && leap(y) ? 29 : DAYS[mo - 1];
  if (d < 1 || d > dim) return null;
  if (h > 23 || mi > 59 || se > 59) return null;
  return daysFromCivil(y, mo, d) * 86400 + h * 3600 + mi * 60 + se;
}
