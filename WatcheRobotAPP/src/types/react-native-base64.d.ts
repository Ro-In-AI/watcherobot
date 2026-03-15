declare module 'react-native-base64' {
  export function encode(str: string): string;
  export function decode(str: string): string;
  export function encodeBytes(arr: number[]): string;
  export function decodeBytes(str: string): number[];
  export function encodeFromByteArray(arr: Uint8Array | number[]): string;
}
