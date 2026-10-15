import type { NextConfig } from "next";

// 브라우저는 같은 출처의 /api만 사용한다. 비밀값과 내부 주소는 서버에 남긴다.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const config: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};
export default config;
