// Utility to safely handle artifact URLs from AI Engine or backend
export function getArtifactUrl(url: string | undefined | null): string {
  if (!url) return '';
  // If absolute path already provided (e.g. from cloud storage), return it.
  if (url.startsWith('http://') || url.startsWith('https://')) {
    // We could proxy it through /files if it's from localhost to avoid CORS.
    // The AI Engine generally returns absolute URLs. If it's a localhost:8000 URL, map it to the vite proxy.
    try {
      const parsedUrl = new URL(url);
      if (parsedUrl.hostname === 'localhost' && parsedUrl.port === '8000') {
        return `/files${parsedUrl.pathname}${parsedUrl.search}`;
      }
      return url;
    } catch {
      return url;
    }
  }
  // Otherwise append to API prefix or proxy prefix
  return url;
}
