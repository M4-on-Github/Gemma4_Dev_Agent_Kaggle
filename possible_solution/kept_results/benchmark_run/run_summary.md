# Claude Code Headless Benchmark Summary

- **Date**: 2026-11-19 07:58:53
- **Model**: `opus5.5`
- **Reasoning Effort**: `high`
- **Tasks Attempted**: 129
- **Tasks Resolved**: 36 / 129 (27.9%)
- **Total Duration**: 60831.8s (1013.9 min)

## Tool Usage Across Tasks

| Tool | Total Calls | Avg Calls / Task |
|---|---:|---:|
| `Bash` | 1425 | 11.0 |
| `Edit` | 167 | 1.3 |
| `Grep` | 68 | 0.5 |
| `Read` | 67 | 0.5 |
| `ToolSearch` | 13 | 0.1 |
| `Write` | 12 | 0.1 |
| `Monitor` | 4 | 0.0 |
| `TaskStop` | 4 | 0.0 |
| `WebFetch` | 3 | 0.0 |

## Per-Task Results

| Task ID | Repo | Resolved | Tool Calls | Patch Bytes | Agent Time | Test Time | Exit |
|---|---|:---:|---:|---:|---:|---:|:---:|
| `fastapi_15661` | `fastapi/fastapi` | **FAIL** | 22 | 15497 B | 212.4s | 9.1s | 4 |
| `fastapi_15588` | `fastapi/fastapi` | **FAIL** | 20 | 3199 B | 140.8s | 10.1s | 4 |
| `fastapi_15589` | `fastapi/fastapi` | **PASS** | 24 | 1760 B | 195.5s | 13.6s | 0 |
| `fastapi_15030` | `fastapi/fastapi` | **FAIL** | 52 | 36753 B | 943.9s | 12.1s | -1 |
| `fastapi_14962` | `fastapi/fastapi` | **FAIL** | 10 | 4036 B | 177.7s | 12.3s | -1 |
| `fastapi_15280` | `fastapi/fastapi` | **FAIL** | 28 | 14324 B | 282.9s | 12.4s | 1 |
| `fastapi_14964` | `fastapi/fastapi` | **FAIL** | 14 | 6358 B | 227.4s | 7.9s | -1 |
| `fastapi_15023` | `fastapi/fastapi` | **FAIL** | 9 | 5639 B | 97.3s | 13.1s | 1 |
| `fastapi_14986` | `fastapi/fastapi` | **FAIL** | 18 | 3826 B | 188.5s | 10.8s | -1 |
| `fastapi_14978` | `fastapi/fastapi` | **FAIL** | 20 | 40392 B | 241.6s | 12.3s | -1 |
| `requests_7505` | `psf/requests` | **FAIL** | 9 | 2794 B | 144.2s | 24.8s | 1 |
| `requests_7502` | `psf/requests` | **FAIL** | 9 | 765 B | 147.5s | 24.1s | 1 |
| `requests_7433` | `psf/requests` | **FAIL** | 7 | 974 B | 102.9s | 25.1s | 1 |
| `requests_7427` | `psf/requests` | **FAIL** | 8 | 1005 B | 79.3s | 3.5s | 1 |
| `requests_7315` | `psf/requests` | **FAIL** | 11 | 522 B | 287.2s | 3.3s | 1 |
| `requests_7328` | `psf/requests` | **FAIL** | 10 | 730 B | 924.8s | 27.6s | 1 |
| `requests_7309` | `psf/requests` | **FAIL** | 5 | 1054 B | 53.6s | 5.4s | 1 |
| `requests_7205` | `psf/requests` | **FAIL** | 4 | 503 B | 39.8s | 9.8s | 1 |
| `rich_4070` | `Textualize/rich` | **FAIL** | 28 | 11169 B | 294.3s | 5.2s | -1 |
| `rich_4077` | `Textualize/rich` | **PASS** | 5 | 810 B | 42.3s | 9.1s | 0 |
| `rich_4079` | `Textualize/rich` | **PASS** | 14 | 1298 B | 140.3s | 8.7s | 0 |
| `rich_4076` | `Textualize/rich` | **FAIL** | 19 | 965 B | 154.0s | 8.2s | 1 |
| `rich_4075` | `Textualize/rich` | **PASS** | 8 | 1022 B | 99.6s | 8.4s | 0 |
| `rich_4006` | `Textualize/rich` | **FAIL** | 5 | 1554 B | 89.5s | 8.3s | 1 |
| `fastapi_14258` | `fastapi/fastapi` | **PASS** | 5 | 590 B | 52.9s | 20.5s | 0 |
| `fastapi_14851` | `fastapi/fastapi` | **FAIL** | 16 | 4178 B | 243.8s | 23.5s | 1 |
| `fastapi_14873` | `fastapi/fastapi` | **PASS** | 8 | 1911 B | 88.2s | 476.9s | 0 |
| `fastapi_13920` | `fastapi/fastapi` | **FAIL** | 20 | 3029 B | 434.9s | 31.5s | 1 |
| `fastapi_14794` | `fastapi/fastapi` | **FAIL** | 10 | 946 B | 350.9s | 32.7s | 1 |
| `fastapi_14786` | `fastapi/fastapi` | **FAIL** | 3 | 404 B | 50.8s | 17.2s | -1 |
| `fastapi_14492` | `fastapi/fastapi` | **FAIL** | 3 | 391 B | 38.9s | 20.5s | 2 |
| `fastapi_14479` | `fastapi/fastapi` | **FAIL** | 9 | 525 B | 124.5s | 21.1s | 1 |
| `fastapi_14463` | `fastapi/fastapi` | **FAIL** | 9 | 1039 B | 311.0s | 27.3s | 2 |
| `fastapi_12942` | `fastapi/fastapi` | **FAIL** | 11 | 983 B | 219.1s | 21.9s | 1 |
| `fastapi_14099` | `fastapi/fastapi` | **FAIL** | 26 | 22227 B | 4083.8s | 8.6s | -1 |
| `fastapi_14609` | `fastapi/fastapi` | **FAIL** | 27 | 13226 B | 730.4s | 12.3s | -1 |
| `fastapi_14372` | `fastapi/fastapi` | **PASS** | 15 | 1687 B | 317.2s | 20.4s | 0 |
| `fastapi_14349` | `fastapi/fastapi` | **FAIL** | 19 | 836 B | 1413.7s | 23.1s | 1 |
| `fastapi_14512` | `fastapi/fastapi` | **FAIL** | 17 | 910 B | 359.3s | 27.4s | 1 |
| `fastapi_14487` | `fastapi/fastapi` | **FAIL** | 13 | 2563 B | 169.6s | 26.6s | 2 |
| `fastapi_11355` | `fastapi/fastapi` | **FAIL** | 25 | 835 B | 1469.3s | 19.0s | 1 |
| `fastapi_14485` | `fastapi/fastapi` | **FAIL** | 11 | 1609 B | 233.4s | 16.1s | 1 |
| `fastapi_14482` | `fastapi/fastapi` | **FAIL** | 30 | 3117 B | 3027.7s | 22.6s | 1 |
| `fastapi_14306` | `fastapi/fastapi` | **FAIL** | 36 | 10106 B | 1541.4s | 17.1s | 2 |
| `fastapi_14458` | `fastapi/fastapi` | **FAIL** | 28 | 2233 B | 3942.9s | 16.6s | 2 |
| `fastapi_14459` | `fastapi/fastapi` | **FAIL** | 22 | 2299 B | 945.3s | 11.3s | -1 |
| `fastapi_14448` | `fastapi/fastapi` | **FAIL** | 20 | 4462 B | 1458.3s | 16.8s | 2 |
| `fastapi_14455` | `fastapi/fastapi` | **FAIL** | 16 | 2385 B | 190.2s | 11.8s | 2 |
| `fastapi_9753` | `fastapi/fastapi` | **FAIL** | 17 | 4405 B | 285.7s | 12.2s | 2 |
| `fastapi_14430` | `fastapi/fastapi` | **FAIL** | 22 | 1170 B | 542.9s | 8.9s | 1 |
| `fastapi_5077` | `fastapi/fastapi` | **FAIL** | 12 | 955 B | 222.7s | 7.1s | -1 |
| `fastapi_9555` | `fastapi/fastapi` | **FAIL** | 14 | 5598 B | 199.4s | 11.6s | 2 |
| `fastapi_14361` | `fastapi/fastapi` | **FAIL** | 12 | 512 B | 154.3s | 11.6s | 1 |
| `fastapi_13207` | `fastapi/fastapi` | **FAIL** | 10 | 2141 B | 164.8s | 11.3s | 1 |
| `fastapi_14360` | `fastapi/fastapi` | **FAIL** | 9 | 626 B | 164.2s | 11.3s | 2 |
| `fastapi_14356` | `fastapi/fastapi` | **FAIL** | 8 | 1117 B | 289.8s | 6.9s | -1 |
| `fastapi_5624` | `fastapi/fastapi` | **FAIL** | 19 | 858 B | 257.3s | 11.9s | 2 |
| `fastapi_14419` | `fastapi/fastapi` | **FAIL** | 10 | 3943 B | 183.6s | 6.6s | -1 |
| `fastapi_14301` | `fastapi/fastapi` | **FAIL** | 21 | 647 B | 264.3s | 11.8s | 2 |
| `fastapi_14262` | `fastapi/fastapi` | **FAIL** | 22 | 13255 B | 341.4s | 7.1s | -1 |
| `fastapi_14266` | `fastapi/fastapi` | **FAIL** | 6 | 2149 B | 106.7s | 11.2s | 2 |
| `fastapi_14246` | `fastapi/fastapi` | **FAIL** | 28 | 2238 B | 444.4s | 6.8s | -1 |
| `fastapi_14186` | `fastapi/fastapi` | **FAIL** | 30 | 26577 B | 600.7s | 6.5s | -1 |
| `fastapi_9425` | `fastapi/fastapi` | **FAIL** | 12 | 710 B | 241.3s | 11.3s | 1 |
| `fastapi_13713` | `fastapi/fastapi` | **FAIL** | 18 | 2844 B | 232.5s | 6.4s | -1 |
| `fastapi_14077` | `fastapi/fastapi` | **FAIL** | 19 | 2689 B | 200.5s | 10.7s | 2 |
| `rich_3718` | `Textualize/rich` | **PASS** | 5 | 767 B | 57.3s | 4.5s | 0 |
| `rich_3934` | `Textualize/rich` | **PASS** | 7 | 2496 B | 85.7s | 6.8s | 0 |
| `rich_3953` | `Textualize/rich` | **PASS** | 26 | 4009 B | 367.9s | 4.8s | 0 |
| `rich_3944` | `Textualize/rich` | **PASS** | 7 | 1152 B | 61.3s | 4.7s | 0 |
| `rich_3942` | `Textualize/rich` | **FAIL** | 12 | 5162 B | 132.8s | 2.4s | -1 |
| `rich_3938` | `Textualize/rich` | **FAIL** | 9 | 1141 B | 98.9s | 2.2s | -1 |
| `rich_3882` | `Textualize/rich` | **PASS** | 5 | 503 B | 39.7s | 4.8s | 0 |
| `rich_3894` | `Textualize/rich` | **PASS** | 11 | 1153 B | 68.3s | 4.8s | 0 |
| `rich_3935` | `Textualize/rich` | **FAIL** | 15 | 536 B | 144.4s | 2.3s | -1 |
| `rich_3905` | `Textualize/rich` | **PASS** | 5 | 1122 B | 46.4s | 5.5s | 0 |
| `rich_3930` | `Textualize/rich` | **FAIL** | 25 | 187617 B | 439.0s | 2.4s | -1 |
| `httpx_3672` | `encode/httpx` | **FAIL** | 19 | 12847 B | 256.2s | 2.9s | 2 |
| `fastapi_14791` | `fastapi/fastapi` | **FAIL** | 4 | 483 B | 44.1s | 6.7s | -1 |
| `fastapi_15800` | `fastapi/fastapi` | **FAIL** | 23 | 22389 B | 450.4s | 14.7s | 1 |
| `fastapi_15785` | `fastapi/fastapi` | **FAIL** | 17 | 6069 B | 218.0s | 13.1s | 1 |
| `fastapi_14371` | `fastapi/fastapi` | **FAIL** | 31 | 8034 B | 524.3s | 7.4s | -1 |
| `fastapi_14605` | `fastapi/fastapi` | **FAIL** | 22 | 8584 B | 342.5s | 7.2s | -1 |
| `fastapi_15763` | `fastapi/fastapi` | **FAIL** | 15 | 1126 B | 261.0s | 13.4s | 1 |
| `fastapi_14583` | `fastapi/fastapi` | **FAIL** | 16 | 2274 B | 231.8s | 7.0s | -1 |
| `fastapi_15745` | `fastapi/fastapi` | **FAIL** | 36 | 27367 B | 636.9s | 7.8s | -1 |
| `fastapi_14297` | `fastapi/fastapi` | **FAIL** | 16 | 1522 B | 17040.7s | 7.0s | -1 |
| `fastapi_14303` | `fastapi/fastapi` | **FAIL** | 17 | 745 B | 281.3s | 12.0s | 2 |
| `fastapi_13537` | `fastapi/fastapi` | **FAIL** | 10 | 604 B | 180.6s | 11.4s | 2 |
| `fastapi_14953` | `fastapi/fastapi` | **FAIL** | 17 | 2377 B | 218.9s | 8.2s | -1 |
| `fastapi_13786` | `fastapi/fastapi` | **FAIL** | 18 | 13294 B | 286.1s | 6.7s | -1 |
| `fastapi_14616` | `fastapi/fastapi` | **FAIL** | 12 | 1749 B | 279.9s | 12.3s | 2 |
| `fastapi_11194` | `fastapi/fastapi` | **FAIL** | 4 | 1020 B | 80.4s | 10.8s | 2 |
| `requests_6757` | `psf/requests` | **FAIL** | 7 | 1576 B | 285.8s | 21.6s | 1 |
| `requests_6629` | `psf/requests` | **FAIL** | 4 | 900 B | 42.5s | 7.4s | 1 |
| `requests_6644` | `psf/requests` | **PASS** | 8 | 524 B | 90.0s | 2.8s | 0 |
| `requests_6589` | `psf/requests` | **FAIL** | 5 | 517 B | 67.3s | 7.3s | 1 |
| `requests_6592` | `psf/requests` | **FAIL** | 4 | 579 B | 48.3s | 7.3s | 1 |
| `rich_3180` | `Textualize/rich` | **FAIL** | 10 | 6494 B | 156.4s | 2.3s | -1 |
| `rich_3486` | `Textualize/rich` | **PASS** | 19 | 4617 B | 211.1s | 5.5s | 0 |
| `rich_3777` | `Textualize/rich` | **PASS** | 9 | 2760 B | 70.0s | 4.9s | 0 |
| `rich_3468` | `Textualize/rich` | **PASS** | 14 | 1947 B | 166.1s | 4.6s | 0 |
| `rich_3782` | `Textualize/rich` | **FAIL** | 16 | 1439 B | 160.9s | 5.4s | 1 |
| `rich_3772` | `Textualize/rich` | **PASS** | 9 | 3936 B | 100.0s | 5.7s | 0 |
| `rich_3296` | `Textualize/rich` | **FAIL** | 8 | 1217 B | 69.2s | 5.6s | 1 |
| `rich_3675` | `Textualize/rich` | **PASS** | 14 | 4716 B | 123.5s | 5.1s | 0 |
| `rich_3676` | `Textualize/rich` | **PASS** | 7 | 2278 B | 64.0s | 5.5s | 0 |
| `rich_3518` | `Textualize/rich` | **PASS** | 7 | 1092 B | 48.9s | 4.7s | 0 |
| `rich_3535` | `Textualize/rich` | **FAIL** | 12 | 489 B | 140.1s | 4.7s | 1 |
| `rich_3521` | `Textualize/rich` | **PASS** | 21 | 1116 B | 237.4s | 4.6s | 0 |
| `rich_3506` | `Textualize/rich` | **PASS** | 6 | 2166 B | 90.7s | 4.7s | 0 |
| `rich_3480` | `Textualize/rich` | **PASS** | 2 | 1643 B | 37.5s | 5.0s | 0 |
| `rich_3472` | `Textualize/rich` | **FAIL** | 5 | 585 B | 48.3s | 4.8s | 1 |
| `rich_3454` | `Textualize/rich` | **PASS** | 4 | 1318 B | 40.6s | 4.4s | 0 |
| `rich_3471` | `Textualize/rich` | **PASS** | 5 | 431 B | 54.7s | 4.9s | 0 |
| `rich_3470` | `Textualize/rich` | **FAIL** | 9 | 1689 B | 95.4s | 4.6s | 1 |
| `rich_3469` | `Textualize/rich` | **FAIL** | 10 | 1282 B | 104.3s | 4.7s | 1 |
| `rich_3052` | `Textualize/rich` | **PASS** | 4 | 5058 B | 52.2s | 4.9s | 0 |
| `rich_3278` | `Textualize/rich` | **PASS** | 7 | 980 B | 58.5s | 4.6s | 0 |
| `rich_2943` | `Textualize/rich` | **PASS** | 6 | 1044 B | 44.2s | 4.6s | 0 |
| `rich_2725` | `Textualize/rich` | **PASS** | 15 | 1670 B | 119.3s | 4.7s | 0 |
| `rich_3105` | `Textualize/rich` | **PASS** | 3 | 941 B | 42.0s | 5.0s | 0 |
| `rich_3130` | `Textualize/rich` | **FAIL** | 12 | 1494 B | 85.0s | 5.3s | 1 |
| `rich_3043` | `Textualize/rich` | **PASS** | 8 | 1098 B | 49.5s | 5.2s | 0 |
| `rich_3067` | `Textualize/rich` | **PASS** | 6 | 1110 B | 46.6s | 4.9s | 0 |
| `rich_3006` | `Textualize/rich` | **PASS** | 5 | 558 B | 35.7s | 4.5s | 0 |
| `rich_3064` | `Textualize/rich` | **FAIL** | 7 | 1495 B | 78.4s | 5.1s | 1 |
| `rich_3063` | `Textualize/rich` | **PASS** | 8 | 925 B | 70.2s | 4.5s | 0 |
| `rich_3061` | `Textualize/rich` | **FAIL** | 16 | 3614 B | 151.5s | 2.3s | -1 |