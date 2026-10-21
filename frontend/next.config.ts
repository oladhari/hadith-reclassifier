import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingIncludes: { "/corpus": ["./.corpus/ara-*.json"] },
};

export default nextConfig;
