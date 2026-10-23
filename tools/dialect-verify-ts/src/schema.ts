// The Core schemas' JSON Schema vocabulary, used only to validate a recording's embedded pack.
// Keeping this reader local preserves the verifier's no-install Node entry point.

type ObjectValue = { [name: string]: unknown };

const objectValue = (value: unknown): value is ObjectValue =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const equal = (left: unknown, right: unknown): boolean => {
  if (left === right) return true;
  if (Array.isArray(left) && Array.isArray(right)) {
    return left.length === right.length && left.every((value, index) => equal(value, right[index]));
  }
  if (objectValue(left) && objectValue(right)) {
    const leftNames = Object.keys(left).sort();
    const rightNames = Object.keys(right).sort();
    return equal(leftNames, rightNames) && leftNames.every((name) => equal(left[name], right[name]));
  }
  return false;
};

const reference = (root: ObjectValue, pointer: string): unknown => {
  if (!pointer.startsWith("#/")) throw new Error(`unsupported schema reference: ${pointer}`);
  let value: unknown = root;
  for (const encoded of pointer.slice(2).split("/")) {
    if (!objectValue(value)) throw new Error(`unresolved schema reference: ${pointer}`);
    const name = encoded.replaceAll("~1", "/").replaceAll("~0", "~");
    value = value[name];
  }
  if (value === undefined) throw new Error(`unresolved schema reference: ${pointer}`);
  return value;
};

const leapYear = (year: number): boolean => year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);

const validDate = (text: string): boolean => {
  const found = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (found === null) return false;
  const year = Number(found[1]);
  const month = Number(found[2]);
  const day = Number(found[3]);
  const days = [31, leapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return month >= 1 && month <= 12 && day >= 1 && day <= days[month - 1]!;
};

const validDateTime = (text: string): boolean => {
  const found = /^(\d{4}-\d{2}-\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:[Zz]|([+-])(\d{2}):(\d{2}))$/.exec(text);
  if (found === null || !validDate(found[1]!)) return false;
  const hour = Number(found[2]);
  const minute = Number(found[3]);
  const second = Number(found[4]);
  if (hour > 23 || minute > 59 || second > 60) return false;
  return found[6] === undefined || (Number(found[6]) <= 23 && Number(found[7]) <= 59);
};

const validUri = (text: string): boolean => {
  const found = /^[A-Za-z][A-Za-z0-9+.-]*:(.*)$/s.exec(text);
  if (found === null || !/^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*$/.test(text) || /%(?![0-9A-Fa-f]{2})/.test(text)) {
    return false;
  }
  const remainder = found[1]!;
  const afterAuthority = remainder.startsWith("//")
    ? remainder.slice(2).replace(/^[^/?#]*/, "")
    : remainder;
  if (/[\[\]]/.test(afterAuthority)) return false;
  try {
    new URL(text);
    return true;
  } catch {
    return false;
  }
};

const validType = (name: string, value: unknown): boolean => {
  switch (name) {
    case "null": return value === null;
    case "boolean": return typeof value === "boolean";
    case "object": return objectValue(value);
    case "array": return Array.isArray(value);
    case "number": return typeof value === "number" && Number.isFinite(value);
    case "integer": return typeof value === "number" && Number.isInteger(value);
    case "string": return typeof value === "string";
    default: throw new Error(`unsupported schema type: ${name}`);
  }
};

const conforms = (given: unknown, value: unknown, root: ObjectValue): boolean => {
  if (typeof given === "boolean") return given;
  if (!objectValue(given)) throw new Error("schema is not an object or boolean");

  if (typeof given.$ref === "string" && !conforms(reference(root, given.$ref), value, root)) return false;
  if ("const" in given && !equal(value, given.const)) return false;
  if (Array.isArray(given.enum) && !given.enum.some((choice) => equal(value, choice))) return false;

  if (typeof given.type === "string" && !validType(given.type, value)) return false;
  if (Array.isArray(given.type) && !given.type.some((name) => typeof name === "string" && validType(name, value))) return false;

  if (Array.isArray(given.allOf) && !given.allOf.every((schema) => conforms(schema, value, root))) return false;
  if (Array.isArray(given.anyOf) && !given.anyOf.some((schema) => conforms(schema, value, root))) return false;
  if (Array.isArray(given.oneOf) && given.oneOf.filter((schema) => conforms(schema, value, root)).length !== 1) return false;
  if (given.not !== undefined && conforms(given.not, value, root)) return false;
  if (given.if !== undefined) {
    const branch = conforms(given.if, value, root) ? given.then : given.else;
    if (branch !== undefined && !conforms(branch, value, root)) return false;
  }

  if (typeof value === "string") {
    if (typeof given.minLength === "number" && [...value].length < given.minLength) return false;
    if (typeof given.pattern === "string" && !new RegExp(given.pattern, "u").test(value)) return false;
    if (given.format === "date" && !validDate(value)) return false;
    if (given.format === "date-time" && !validDateTime(value)) return false;
    if (given.format === "uri" && !validUri(value)) return false;
  }

  if (Array.isArray(value)) {
    if (typeof given.minItems === "number" && value.length < given.minItems) return false;
    if (typeof given.maxItems === "number" && value.length > given.maxItems) return false;
    if (given.uniqueItems === true && value.some((item, index) => value.slice(0, index).some((prior) => equal(item, prior)))) return false;
    if (given.items !== undefined && !value.every((item) => conforms(given.items, item, root))) return false;
    if (given.contains !== undefined && !value.some((item) => conforms(given.contains, item, root))) return false;
  }

  if (objectValue(value)) {
    if (Array.isArray(given.required) && !given.required.every((name) => typeof name === "string" && Object.hasOwn(value, name))) return false;
    const properties = objectValue(given.properties) ? given.properties : {};
    for (const [name, member] of Object.entries(value)) {
      if (Object.hasOwn(properties, name)) {
        if (!conforms(properties[name], member, root)) return false;
      } else if (given.additionalProperties === false) {
        return false;
      } else if (given.additionalProperties !== undefined && given.additionalProperties !== true && !conforms(given.additionalProperties, member, root)) {
        return false;
      }
      if (given.propertyNames !== undefined && !conforms(given.propertyNames, name, root)) return false;
    }
  }

  return true;
};

export const validates = (schema: unknown, value: unknown): boolean => {
  if (!objectValue(schema)) throw new Error("root schema is not an object");
  return conforms(schema, value, schema);
};
