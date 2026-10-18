// §5.1: the constrained page form and prefix comparison. No URL parser or path decoding.
export function pageEndpoint(value: string): [string, string] | undefined {
  if (value.length > 2048 || /[^\x21-\x7e]/.test(value)) return undefined;
  const match = /^https:\/\/([A-Za-z0-9.-]+)(?::(?:443)?)?(\/[^?#\\]*)?$/.exec(value);
  if (match === null) return undefined;
  const host = match[1];
  const path = match[2] ?? "";
  const labels = host.split(".");
  if (labels.length < 2 || !/^[A-Za-z]/.test(labels.at(-1)!)) return undefined;
  if (labels.some((s) => !/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/.test(s))) {
    return undefined;
  }
  if (/%(?![0-9A-Fa-f]{2})/.test(path)) return undefined;
  if (/%(?:2[fF]|5[cC])/.test(path)) return undefined; // Round 16: an escaped slash or backslash.
  // A dot segment, alone or before the first `;` or escaped delimiter of its segment (round 16).
  const head = (s: string) => s.split(/;|%3[bBfF]|%23|%00/, 1)[0];
  if (path.split("/").some((s) => /^(?:\.|%2[eE]){1,2}$/.test(head(s)))) return undefined;
  return [host.toLowerCase(), path]; // ASCII host comparison; signed bytes stay as written.
}

export function endpointInScope(endpoint: string, scope: string[]): boolean {
  const parsed = pageEndpoint(endpoint);
  if (parsed === undefined) return false;
  const [host, path] = parsed;
  return scope.some((entry) => {
    if (entry === "https://*") return true;
    const [otherHost, prefix] = pageEndpoint(entry)!; // Profile form was checked first.
    return host === otherHost && (
      prefix === "" || prefix === "/" || path === prefix
      || path.startsWith(prefix.endsWith("/") ? prefix : prefix + "/")
    );
  });
}
