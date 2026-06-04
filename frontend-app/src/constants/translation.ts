export const TRANSLATION_LANGUAGE_OPTIONS = [
  { code: 'auto', label: 'Auto Detect' },
  { code: 'en-IN', label: 'English' },
  { code: 'hi-IN', label: 'Hindi' },
  { code: 'ta-IN', label: 'Tamil' },
  { code: 'te-IN', label: 'Telugu' },
  { code: 'kn-IN', label: 'Kannada' },
  { code: 'ml-IN', label: 'Malayalam' },
  { code: 'bn-IN', label: 'Bengali' },
  { code: 'mr-IN', label: 'Marathi' },
  { code: 'gu-IN', label: 'Gujarati' },
  { code: 'pa-IN', label: 'Punjabi' },
] as const;

export const DEFAULT_CALLER_LANGUAGE = 'hi-IN';
export const DEFAULT_USER_LANGUAGE = 'en-IN';

export function getLanguageLabel(code: string) {
  return TRANSLATION_LANGUAGE_OPTIONS.find((option) => option.code === code)?.label || code;
}
