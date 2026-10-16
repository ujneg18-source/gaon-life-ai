/** 시연 초기화는 앱 소유 브라우저 상태만 비운다. 인증 쿠키는 서버가 관리한다. */
export function clearDemoSession(revision: string) {
  for (const storage of [localStorage, sessionStorage]) {
    for (const key of Object.keys(storage)) {
      if (
        key !== "gaon-demo-revision" &&
        /^(gaon[-:]|onboarding[-:]|chat[-:])/.test(key)
      )
        storage.removeItem(key);
    }
  }
  sessionStorage.removeItem("inbox-return");
  localStorage.setItem("gaon-demo-revision", revision);
}
