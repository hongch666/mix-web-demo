declare module 'qs' {
  export interface IStringifyOptions {
    delimiter?: string;
    strictNullHandling?: boolean;
    skipNulls?: boolean;
    encode?: boolean;
    encoder?: (str: string) => string;
    filter?: Array<string | number> | ((prefix: string, value: any) => any);
    arrayFormat?: 'indices' | 'brackets' | 'repeat' | 'comma';
    indices?: boolean;
    sort?: (a: string, b: string) => number;
    serializeDate?: (date: Date) => string;
    format?: 'RFC1738' | 'RFC3986';
    encoder?: (str: string) => string;
    encodeValuesOnly?: boolean;
    addQueryPrefix?: boolean;
    allowDots?: boolean;
    charset?: string;
    charsetSentinel?: boolean;
  }

  export interface IParseOptions {
    comma?: boolean;
    delimiter?: string | RegExp;
    depth?: number;
    decoder?: (str: string) => string;
    arrayLimit?: number;
    parseArrays?: boolean;
    allowDots?: boolean;
    plainObjects?: boolean;
    allowPrototypes?: boolean;
    parameterLimit?: number;
    strictNullHandling?: boolean;
    ignoreQueryPrefix?: boolean;
    charset?: string;
    charsetSentinel?: boolean;
    interpretNumericEntities?: boolean;
  }

  export function stringify(obj: any, options?: IStringifyOptions): string;
  export function parse(str: string, options?: IParseOptions): any;

  const qs: {
    stringify: typeof stringify;
    parse: typeof parse;
  };

  export = qs;
}
