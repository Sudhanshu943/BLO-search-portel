/** @type {import('next').NextConfig} */
const nextConfig = {
  // Key moved from experimental to the root in Next.js 16
  serverExternalPackages: ["pdfplumber", "PyPDF2"],

  // Configuration for local network access
  devIndicators: {
    appIsrStatus: false,
  },

  experimental: {
    // If your version still warns about this, it is likely 
    // because Next.js 16 handles dev origins automatically 
    // or through a different internal mechanism.
    // You can try removing this line if the warning persists.
    allowedDevOrigins: ["http://192.168.1.12:3000", "http://localhost:3000"],
  },
};

export default nextConfig;