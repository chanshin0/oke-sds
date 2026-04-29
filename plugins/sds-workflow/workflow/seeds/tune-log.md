# tune-log — /tune 피드백 적용 이력

`/tune` 이 피드백을 접수할 때마다 아래 포맷으로 엔트리를 append 한다.

포맷:

```
## YYYY-MM-DD — <제목>

- 카테고리: command-behavior | template | config | config-local | design-principle
- 대상: <파일 경로>
- 상태: applied | deferred | rejected
- 사유: <한두 줄>
```

---

(엔트리 없음. `/tune "피드백"` 실행 시 자동 추가된다.)
