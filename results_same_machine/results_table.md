| Method | n | EM hits | EM | F1 | F1 sd | Mean prompt tokens | Token reduction vs Part 1 | Compress lat (s) | Generate lat (s) | Total lat (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| Uncompressed | 150 | 14 | 0.0933 | 0.4296 | 0.2910 | 6966.8 | - | 0.000 | 4.63 | 4.65 |
| Head-tail 2x | 150 | 11 | 0.0733 | 0.4065 | 0.2931 | 3523.1 | 49.4% | 0.019 | 5.79 | 5.82 |
| Head-tail 4x | 150 | 10 | 0.0667 | 0.3620 | 0.2978 | 1801.2 | 74.1% | 0.018 | 3.52 | 3.55 |
| LLMLingua 2x | 150 | 1 | 0.0067 | 0.2626 | 0.2675 | 3308.1 | 52.5% | 10.816 | 3.02 | 13.84 |
| LLMLingua 4x | 150 | 2 | 0.0133 | 0.2207 | 0.2396 | 1961.6 | 71.8% | 9.846 | 2.13 | 11.98 |

Paired F1 differences (second minus first, paired by id, 95% CI = mean +/- 1.96 SE):

| Contrast | n paired | Mean dF1 | 95% CI | Verdict |
|---|---:|---:|---|---|
| Uncompressed -> Head-tail 2x | 150 | -0.0231 | [-0.057, +0.011] | Not significant |
| Uncompressed -> Head-tail 4x | 150 | -0.0676 | [-0.107, -0.028] | Significant |
| Uncompressed -> LLMLingua 2x | 150 | -0.1670 | [-0.208, -0.127] | Significant |
| Uncompressed -> LLMLingua 4x | 150 | -0.2090 | [-0.250, -0.168] | Significant |
| Head-tail 2x -> LLMLingua 2x | 150 | -0.1440 | [-0.186, -0.102] | Significant |
| Head-tail 4x -> LLMLingua 4x | 150 | -0.1414 | [-0.183, -0.100] | Significant |

Note: latencies come from the machine(s) that produced each file; compare them only within one part unless all files come from the same GPU.
