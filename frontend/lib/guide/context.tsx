"use client";
import { createContext, useContext } from "react";
/** 실제 업무 화면에는 제공하지 않는 읽기 전용 안내 데이터 경계. */
export const GuideContext = createContext<{
  resolve: (url: string) => unknown;
} | null>(null);
export const useGuide = () => useContext(GuideContext);
