# Lessons, E4B

- R-000 (2026-11-18): base resolves 4 and 7 of 56 on cdev-56. 14-18% of tasks end with an empty patch
  although `submit_patch` is called on 95%+; 17-28% of edit calls fail.
- R-001/R-002: one tree's two draws differ by up to 6 resolves (11 vs 5; 6 vs 2). Two draws of 56
  tasks cannot rank E4B trees; use three and pool the base.
- R-002: adding rules to the 3.1 kB prompt did not change edit behaviour. Next: fewer rules, not more.
- R-003/R-004: temperature 0.3, a short prompt and thoughts-out-of-history all score at the base
  (5.7, 6.0, 5.0 vs 6.0). The E4B is insensitive to prompt length and sampling at this level.
- R-001 at three draws: calls40 and sweep both 8.0 vs 6.0, exactly at the keep threshold. Treated as
  unproven until the compose run (R-006).

- 2026-11-18 R-006: sweep + calls40 composed scores 8, 4, 8 (6.7) against base 6.0. The two +2.0
  three-draw results were noise. On cdev-56 a three-draw mean must beat the base by 3 to be kept.
