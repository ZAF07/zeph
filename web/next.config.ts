import type { NextConfig } from "next";

import { checkServerSettings } from "@/env";

checkServerSettings();

const nextConfig: NextConfig = {};

export default nextConfig;
