## test split (371 tasks): controllers, mean [95% task-cluster bootstrap CI]

| controller | accuracy | s/task | token-compute/task |
|---|---|---|---|
| strong-only | 0.751 [0.710, 0.790] | 16.8 [15.8, 18.0] | 3749 [3604, 3908] |
| local-only | 0.629 [0.589, 0.671] | 3.2 [3.0, 3.4] | 761 [731, 792] |
| visible->reroute | 0.765 [0.727, 0.804] | 8.4 [7.3, 9.5] | 1821 [1635, 2006] |
| visible->resample(2)->reroute | 0.774 [0.736, 0.812] | 7.9 [6.8, 9.1] | 1725 [1514, 1933] |
| visible->resample(3)->reroute | 0.778 [0.739, 0.816] | 8.1 [6.9, 9.5] | 1766 [1531, 2004] |
| visible->resample(4)->reroute | 0.781 [0.742, 0.819] | 8.5 [7.0, 10.0] | 1830 [1568, 2097] |
| visible->resample(5)->reroute | 0.784 [0.745, 0.823] | 8.8 [7.3, 10.4] | 1905 [1615, 2200] |
| [transfer] tev->reroute | 0.748 [0.707, 0.786] | 12.4 [11.3, 13.6] | 3866 [3661, 4087] |
| [transfer] tev->resample(2)->reroute | 0.748 [0.708, 0.785] | 13.2 [11.9, 14.6] | 4523 [4224, 4829] |
| [transfer] tev->resample(3)->reroute | 0.752 [0.711, 0.790] | 14.2 [12.7, 15.9] | 5148 [4754, 5547] |
| [transfer] tev->resample(4)->reroute | 0.753 [0.712, 0.791] | 15.5 [13.7, 17.3] | 5764 [5272, 6258] |
| [transfer] tev->resample(5)->reroute | 0.752 [0.711, 0.791] | 16.6 [14.7, 18.8] | 6357 [5770, 6949] |
| [transfer] llama->reroute | 0.742 [0.702, 0.780] | 18.0 [16.7, 19.5] | 5321 [5017, 5632] |
| [transfer] selfconf->reroute | 0.748 [0.707, 0.786] | 16.6 [15.5, 17.7] | 3779 [3620, 3935] |
| [transfer] vis&tev->reroute | 0.766 [0.726, 0.804] | 12.7 [11.6, 13.9] | 3634 [3465, 3817] |
| [transfer] vis&llama->reroute | 0.758 [0.718, 0.797] | 18.0 [16.7, 19.5] | 4956 [4699, 5239] |
| [transfer] vis&selfconf->reroute | 0.751 [0.711, 0.789] | 16.9 [15.7, 18.0] | 3841 [3674, 4004] |
| [transfer] tev&sc@frozen->reroute | 0.750 [0.710, 0.789] | 18.4 [17.3, 19.6] | 5265 [5075, 5463] |
| [transfer] tev|sc@frozen->reroute | 0.745 [0.705, 0.784] | 12.1 [11.0, 13.2] | 3778 [3585, 3981] |
| [recal] tev->reroute | 0.748 [0.707, 0.786] | 12.4 [11.3, 13.6] | 3866 [3661, 4087] |
| [recal] tev->resample(2)->reroute | 0.748 [0.708, 0.785] | 13.2 [11.9, 14.6] | 4523 [4224, 4829] |
| [recal] tev->resample(3)->reroute | 0.752 [0.711, 0.790] | 14.2 [12.7, 15.9] | 5148 [4754, 5547] |
| [recal] tev->resample(4)->reroute | 0.753 [0.712, 0.791] | 15.5 [13.7, 17.3] | 5764 [5272, 6258] |
| [recal] tev->resample(5)->reroute | 0.752 [0.711, 0.791] | 16.6 [14.7, 18.8] | 6357 [5770, 6949] |
| [recal] llama->reroute | 0.742 [0.702, 0.780] | 18.0 [16.7, 19.5] | 5321 [5017, 5632] |
| [recal] selfconf->reroute | 0.748 [0.707, 0.786] | 16.6 [15.5, 17.7] | 3779 [3620, 3935] |
| [recal] vis&tev->reroute | 0.765 [0.727, 0.804] | 9.5 [8.4, 10.5] | 2835 [2680, 2998] |
| [recal] vis&llama->reroute | 0.766 [0.727, 0.804] | 9.6 [8.6, 10.7] | 3066 [2905, 3235] |
| [recal] vis&selfconf->reroute | 0.765 [0.727, 0.804] | 8.4 [7.3, 9.5] | 1821 [1635, 2006] |
| [recal] tev&sc->reroute | 0.746 [0.706, 0.784] | 13.3 [12.2, 14.4] | 4114 [3932, 4306] |
| [recal] tev|sc->reroute | 0.741 [0.701, 0.779] | 14.5 [13.5, 15.5] | 4366 [4184, 4537] |
| cascade 3B->7B->14B gate visible | 0.780 [0.741, 0.817] | 8.3 [7.1, 9.6] | 1809 [1587, 2041] |
| cascade 3B->7B->14B gate tev [transfer] | 0.750 [0.710, 0.788] | 15.2 [13.7, 16.8] | 4939 [4606, 5281] |
| cascade 3B->7B->14B gate vis&tev [transfer] | 0.772 [0.732, 0.810] | 15.5 [14.1, 17.1] | 4591 [4330, 4864] |

### test: paired differences

| comparison | accuracy | s/task | token-compute |
|---|---|---|---|
| strong-only minus visible->reroute | -0.014 [-0.034, +0.006] | +8.4 [+7.5, +9.4] | +1928 [+1763, +2100] |
| local-only minus strong-only | -0.121 [-0.156, -0.089] | -13.6 [-14.6, -12.7] | -2987 [-3116, -2869] |
| local-only minus visible->reroute | -0.136 [-0.163, -0.111] | -5.2 [-6.2, -4.2] | -1060 [-1228, -889] |
| visible->reroute minus strong-only | +0.014 [-0.006, +0.034] | -8.4 [-9.4, -7.5] | -1928 [-2100, -1763] |
| visible->resample(2)->reroute minus strong-only | +0.023 [-0.001, +0.047] | -8.9 [-10.0, -7.8] | -2024 [-2219, -1835] |
| visible->resample(2)->reroute minus visible->reroute | +0.009 [+0.003, +0.015] | -0.5 [-0.7, -0.2] | -96 [-144, -47] |
| visible->resample(3)->reroute minus strong-only | +0.027 [+0.001, +0.053] | -8.7 [-9.9, -7.5] | -1983 [-2197, -1771] |
| visible->resample(3)->reroute minus visible->reroute | +0.013 [+0.004, +0.022] | -0.3 [-0.7, +0.2] | -55 [-133, +30] |
| visible->resample(4)->reroute minus strong-only | +0.030 [+0.002, +0.057] | -8.4 [-9.7, -7.0] | -1918 [-2159, -1680] |
| visible->resample(4)->reroute minus visible->reroute | +0.016 [+0.005, +0.027] | +0.1 [-0.5, +0.7] | +9 [-96, +128] |
| visible->resample(5)->reroute minus strong-only | +0.033 [+0.005, +0.061] | -8.0 [-9.5, -6.6] | -1844 [-2106, -1575] |
| visible->resample(5)->reroute minus visible->reroute | +0.019 [+0.007, +0.032] | +0.4 [-0.3, +1.2] | +84 [-50, +232] |
| [transfer] tev->reroute minus strong-only | -0.003 [-0.019, +0.013] | -4.4 [-5.4, -3.4] | +117 [-66, +291] |
| [transfer] tev->reroute minus visible->reroute | -0.018 [-0.031, -0.004] | +4.0 [+3.4, +4.6] | +2045 [+1912, +2184] |
| [transfer] tev->resample(2)->reroute minus strong-only | -0.003 [-0.021, +0.017] | -3.7 [-4.9, -2.4] | +774 [+495, +1044] |
| [transfer] tev->resample(2)->reroute minus visible->reroute | -0.017 [-0.031, -0.003] | +4.8 [+4.0, +5.6] | +2702 [+2497, +2915] |
| [transfer] tev->resample(3)->reroute minus strong-only | +0.001 [-0.019, +0.022] | -2.6 [-4.1, -1.2] | +1399 [+1026, +1761] |
| [transfer] tev->resample(3)->reroute minus visible->reroute | -0.013 [-0.027, +0.002] | +5.8 [+4.9, +6.8] | +3327 [+3033, +3625] |
| [transfer] tev->resample(4)->reroute minus strong-only | +0.002 [-0.020, +0.024] | -1.4 [-3.0, +0.3] | +2015 [+1555, +2470] |
| [transfer] tev->resample(4)->reroute minus visible->reroute | -0.013 [-0.028, +0.004] | +7.0 [+5.8, +8.2] | +3943 [+3552, +4338] |
| [transfer] tev->resample(5)->reroute minus strong-only | +0.001 [-0.022, +0.024] | -0.2 [-2.1, +1.7] | +2608 [+2046, +3164] |
| [transfer] tev->resample(5)->reroute minus visible->reroute | -0.014 [-0.029, +0.004] | +8.2 [+6.8, +9.7] | +4536 [+4051, +5033] |
| [transfer] llama->reroute minus strong-only | -0.009 [-0.021, +0.002] | +1.2 [+0.5, +1.8] | +1573 [+1391, +1756] |
| [transfer] llama->reroute minus visible->reroute | -0.023 [-0.041, -0.005] | +9.6 [+8.5, +10.7] | +3500 [+3253, +3767] |
| [transfer] selfconf->reroute minus strong-only | -0.003 [-0.010, +0.003] | -0.3 [-1.0, +0.4] | +31 [-107, +155] |
| [transfer] selfconf->reroute minus visible->reroute | -0.018 [-0.036, +0.002] | +8.2 [+7.4, +8.9] | +1958 [+1810, +2111] |
| [transfer] vis&tev->reroute minus strong-only | +0.015 [+0.000, +0.029] | -4.1 [-5.1, -3.2] | -114 [-252, +37] |
| [transfer] vis&tev->reroute minus visible->reroute | +0.000 [-0.011, +0.013] | +4.3 [+3.8, +4.9] | +1814 [+1683, +1952] |
| [transfer] vis&llama->reroute minus strong-only | +0.007 [-0.001, +0.015] | +1.2 [+0.6, +1.8] | +1207 [+1054, +1362] |
| [transfer] vis&llama->reroute minus visible->reroute | -0.007 [-0.024, +0.010] | +9.6 [+8.6, +10.7] | +3135 [+2874, +3406] |
| [transfer] vis&selfconf->reroute minus strong-only | +0.000 [-0.005, +0.006] | +0.0 [-0.7, +0.6] | +92 [-39, +214] |
| [transfer] vis&selfconf->reroute minus visible->reroute | -0.014 [-0.032, +0.005] | +8.4 [+7.7, +9.2] | +2020 [+1880, +2154] |
| [transfer] tev&sc@frozen->reroute minus strong-only | -0.001 [-0.007, +0.005] | +1.6 [+0.9, +2.2] | +1516 [+1392, +1629] |
| [transfer] tev&sc@frozen->reroute minus visible->reroute | -0.015 [-0.033, +0.005] | +10.0 [+9.2, +10.7] | +3444 [+3296, +3592] |
| [transfer] tev|sc@frozen->reroute minus strong-only | -0.006 [-0.022, +0.010] | -4.8 [-5.8, -3.8] | +30 [-139, +198] |
| [transfer] tev|sc@frozen->reroute minus visible->reroute | -0.020 [-0.034, -0.006] | +3.6 [+3.1, +4.3] | +1957 [+1827, +2090] |
| [recal] tev->reroute minus strong-only | -0.003 [-0.019, +0.013] | -4.4 [-5.4, -3.4] | +117 [-66, +291] |
| [recal] tev->reroute minus visible->reroute | -0.018 [-0.031, -0.004] | +4.0 [+3.4, +4.6] | +2045 [+1912, +2184] |
| [recal] tev->resample(2)->reroute minus strong-only | -0.003 [-0.021, +0.017] | -3.7 [-4.9, -2.4] | +774 [+495, +1044] |
| [recal] tev->resample(2)->reroute minus visible->reroute | -0.017 [-0.031, -0.003] | +4.8 [+4.0, +5.6] | +2702 [+2497, +2915] |
| [recal] tev->resample(3)->reroute minus strong-only | +0.001 [-0.019, +0.022] | -2.6 [-4.1, -1.2] | +1399 [+1026, +1761] |
| [recal] tev->resample(3)->reroute minus visible->reroute | -0.013 [-0.027, +0.002] | +5.8 [+4.9, +6.8] | +3327 [+3033, +3625] |
| [recal] tev->resample(4)->reroute minus strong-only | +0.002 [-0.020, +0.024] | -1.4 [-3.0, +0.3] | +2015 [+1555, +2470] |
| [recal] tev->resample(4)->reroute minus visible->reroute | -0.013 [-0.028, +0.004] | +7.0 [+5.8, +8.2] | +3943 [+3552, +4338] |
| [recal] tev->resample(5)->reroute minus strong-only | +0.001 [-0.022, +0.024] | -0.2 [-2.1, +1.7] | +2608 [+2046, +3164] |
| [recal] tev->resample(5)->reroute minus visible->reroute | -0.014 [-0.029, +0.004] | +8.2 [+6.8, +9.7] | +4536 [+4051, +5033] |
| [recal] llama->reroute minus strong-only | -0.009 [-0.021, +0.002] | +1.2 [+0.5, +1.8] | +1573 [+1391, +1756] |
| [recal] llama->reroute minus visible->reroute | -0.023 [-0.041, -0.005] | +9.6 [+8.5, +10.7] | +3500 [+3253, +3767] |
| [recal] selfconf->reroute minus strong-only | -0.003 [-0.010, +0.003] | -0.3 [-1.0, +0.4] | +31 [-107, +155] |
| [recal] selfconf->reroute minus visible->reroute | -0.018 [-0.036, +0.002] | +8.2 [+7.4, +8.9] | +1958 [+1810, +2111] |
| [recal] vis&tev->reroute minus strong-only | +0.014 [-0.006, +0.034] | -7.4 [-8.3, -6.5] | -913 [-1025, -806] |
| [recal] vis&tev->reroute minus visible->reroute | +0.000 [+0.000, +0.000] | +1.1 [+1.0, +1.1] | +1014 [+952, +1079] |
| [recal] vis&llama->reroute minus strong-only | +0.015 [-0.006, +0.034] | -7.3 [-8.2, -6.4] | -682 [-774, -591] |
| [recal] vis&llama->reroute minus visible->reroute | +0.000 [+0.000, +0.001] | +1.2 [+1.1, +1.3] | +1245 [+1158, +1336] |
| [recal] vis&selfconf->reroute minus strong-only | +0.014 [-0.006, +0.034] | -8.4 [-9.4, -7.5] | -1928 [-2100, -1763] |
| [recal] vis&selfconf->reroute minus visible->reroute | +0.000 [+0.000, +0.000] | +0.0 [+0.0, +0.0] | +0 [+0, +0] |
| [recal] tev&sc->reroute minus strong-only | -0.005 [-0.018, +0.008] | -3.6 [-4.6, -2.6] | +365 [+194, +529] |
| [recal] tev&sc->reroute minus visible->reroute | -0.019 [-0.034, -0.005] | +4.9 [+4.3, +5.4] | +2293 [+2180, +2408] |
| [recal] tev|sc->reroute minus strong-only | -0.010 [-0.020, +0.001] | -2.4 [-3.3, -1.5] | +617 [+453, +771] |
| [recal] tev|sc->reroute minus visible->reroute | -0.024 [-0.042, -0.005] | +6.0 [+5.3, +6.8] | +2545 [+2401, +2683] |
| cascade 3B->7B->14B gate visible minus strong-only | +0.029 [+0.005, +0.054] | -8.5 [-9.7, -7.4] | -1939 [-2143, -1734] |
| cascade 3B->7B->14B gate visible minus visible->reroute | +0.015 [+0.006, +0.024] | -0.1 [-0.5, +0.3] | -12 [-89, +70] |
| cascade 3B->7B->14B gate tev [transfer] minus strong-only | -0.001 [-0.019, +0.017] | -1.6 [-3.0, -0.3] | +1190 [+873, +1483] |
| cascade 3B->7B->14B gate tev [transfer] minus visible->reroute | -0.015 [-0.029, -0.000] | +6.8 [+5.9, +7.7] | +3118 [+2882, +3359] |
| cascade 3B->7B->14B gate vis&tev [transfer] minus strong-only | +0.021 [+0.004, +0.037] | -1.3 [-2.7, +0.0] | +842 [+590, +1097] |
| cascade 3B->7B->14B gate vis&tev [transfer] minus visible->reroute | +0.006 [-0.006, +0.019] | +7.1 [+6.3, +8.0] | +2770 [+2576, +2971] |

## cal split (171 tasks): controllers, mean [95% task-cluster bootstrap CI]

| controller | accuracy | s/task | token-compute/task |
|---|---|---|---|
| strong-only | 0.794 [0.742, 0.846] | 18.1 [16.3, 20.2] | 3873 [3623, 4148] |
| local-only | 0.702 [0.645, 0.754] | 3.6 [3.3, 4.0] | 779 [730, 833] |
| visible->reroute | 0.834 [0.785, 0.878] | 8.5 [7.2, 9.9] | 1763 [1533, 2001] |
| visible->resample(2)->reroute | 0.838 [0.788, 0.882] | 7.7 [6.4, 9.2] | 1588 [1358, 1834] |
| visible->resample(3)->reroute | 0.839 [0.789, 0.884] | 7.5 [6.2, 9.1] | 1551 [1316, 1820] |
| visible->resample(4)->reroute | 0.842 [0.792, 0.886] | 7.5 [6.1, 9.2] | 1554 [1300, 1844] |
| visible->resample(5)->reroute | 0.842 [0.791, 0.887] | 7.7 [6.2, 9.4] | 1583 [1309, 1893] |
| [transfer] tev->reroute | 0.803 [0.753, 0.848] | 12.8 [11.2, 14.4] | 3676 [3395, 3967] |
| [transfer] tev->resample(2)->reroute | 0.800 [0.750, 0.846] | 13.3 [11.4, 15.3] | 4169 [3787, 4565] |
| [transfer] tev->resample(3)->reroute | 0.797 [0.747, 0.844] | 14.3 [12.1, 16.6] | 4656 [4172, 5161] |
| [transfer] tev->resample(4)->reroute | 0.795 [0.744, 0.841] | 15.3 [12.8, 18.0] | 5121 [4521, 5757] |
| [transfer] tev->resample(5)->reroute | 0.790 [0.739, 0.838] | 16.4 [13.6, 19.4] | 5574 [4848, 6327] |
| [transfer] llama->reroute | 0.795 [0.745, 0.845] | 20.3 [17.9, 22.8] | 5546 [5062, 6066] |
| [transfer] selfconf->reroute | 0.788 [0.736, 0.840] | 17.4 [15.8, 19.1] | 3835 [3610, 4080] |
| [transfer] vis&tev->reroute | 0.827 [0.780, 0.873] | 13.4 [11.8, 15.0] | 3582 [3321, 3846] |
| [transfer] vis&llama->reroute | 0.805 [0.755, 0.855] | 20.2 [17.9, 22.8] | 5206 [4763, 5683] |
| [transfer] vis&selfconf->reroute | 0.798 [0.745, 0.849] | 17.8 [16.2, 19.5] | 3921 [3682, 4180] |
| [transfer] tev&sc@frozen->reroute | 0.792 [0.739, 0.844] | 19.5 [17.8, 21.3] | 5238 [4961, 5547] |
| [transfer] tev|sc@frozen->reroute | 0.799 [0.751, 0.844] | 12.3 [10.8, 13.8] | 3585 [3316, 3868] |
| [recal] tev->reroute | 0.803 [0.753, 0.848] | 12.8 [11.2, 14.4] | 3676 [3395, 3967] |
| [recal] tev->resample(2)->reroute | 0.800 [0.750, 0.846] | 13.3 [11.4, 15.3] | 4169 [3787, 4565] |
| [recal] tev->resample(3)->reroute | 0.797 [0.747, 0.844] | 14.3 [12.1, 16.6] | 4656 [4172, 5161] |
| [recal] tev->resample(4)->reroute | 0.795 [0.744, 0.841] | 15.3 [12.8, 18.0] | 5121 [4521, 5757] |
| [recal] tev->resample(5)->reroute | 0.790 [0.739, 0.838] | 16.4 [13.6, 19.4] | 5574 [4848, 6327] |
| [recal] llama->reroute | 0.795 [0.745, 0.845] | 20.3 [17.9, 22.8] | 5546 [5062, 6066] |
| [recal] selfconf->reroute | 0.788 [0.736, 0.840] | 17.4 [15.8, 19.1] | 3835 [3610, 4080] |
| [recal] vis&tev->reroute | 0.834 [0.785, 0.878] | 9.7 [8.4, 11.0] | 2735 [2520, 2961] |
| [recal] vis&llama->reroute | 0.834 [0.785, 0.878] | 9.7 [8.4, 11.0] | 2956 [2715, 3201] |
| [recal] vis&selfconf->reroute | 0.834 [0.785, 0.878] | 8.5 [7.2, 9.9] | 1763 [1533, 2001] |
| [recal] tev&sc->reroute | 0.803 [0.754, 0.850] | 13.3 [11.9, 14.8] | 3852 [3621, 4096] |
| [recal] tev|sc->reroute | 0.798 [0.749, 0.846] | 15.3 [13.9, 16.8] | 4317 [4069, 4566] |
| cascade 3B->7B->14B gate visible | 0.851 [0.806, 0.893] | 7.6 [6.4, 9.0] | 1636 [1402, 1895] |
| cascade 3B->7B->14B gate tev [transfer] | 0.804 [0.754, 0.851] | 15.0 [13.0, 17.3] | 4559 [4127, 5012] |
| cascade 3B->7B->14B gate vis&tev [transfer] | 0.835 [0.786, 0.880] | 15.7 [13.6, 17.9] | 4440 [4055, 4855] |

### cal: paired differences

| comparison | accuracy | s/task | token-compute |
|---|---|---|---|
| strong-only minus visible->reroute | -0.039 [-0.070, -0.010] | +9.6 [+8.0, +11.3] | +2110 [+1853, +2382] |
| local-only minus strong-only | -0.093 [-0.142, -0.047] | -14.5 [-16.3, -12.9] | -3094 [-3320, -2893] |
| local-only minus visible->reroute | -0.132 [-0.165, -0.101] | -4.9 [-6.2, -3.8] | -983 [-1212, -781] |
| visible->reroute minus strong-only | +0.039 [+0.010, +0.070] | -9.6 [-11.3, -8.0] | -2110 [-2382, -1853] |
| visible->resample(2)->reroute minus strong-only | +0.044 [+0.008, +0.078] | -10.4 [-12.3, -8.7] | -2285 [-2566, -2016] |
| visible->resample(2)->reroute minus visible->reroute | +0.004 [-0.005, +0.013] | -0.8 [-1.2, -0.5] | -175 [-242, -108] |
| visible->resample(3)->reroute minus strong-only | +0.045 [+0.007, +0.082] | -10.6 [-12.5, -8.8] | -2322 [-2623, -2035] |
| visible->resample(3)->reroute minus visible->reroute | +0.006 [-0.006, +0.018] | -1.0 [-1.5, -0.4] | -212 [-317, -105] |
| visible->resample(4)->reroute minus strong-only | +0.047 [+0.008, +0.086] | -10.6 [-12.6, -8.6] | -2319 [-2636, -2009] |
| visible->resample(4)->reroute minus visible->reroute | +0.008 [-0.006, +0.023] | -1.0 [-1.7, -0.3] | -208 [-339, -65] |
| visible->resample(5)->reroute minus strong-only | +0.048 [+0.007, +0.088] | -10.4 [-12.5, -8.4] | -2290 [-2621, -1954] |
| visible->resample(5)->reroute minus visible->reroute | +0.008 [-0.007, +0.024] | -0.8 [-1.6, +0.0] | -180 [-331, -10] |
| [transfer] tev->reroute minus strong-only | +0.009 [-0.015, +0.034] | -5.3 [-7.2, -3.7] | -197 [-484, +82] |
| [transfer] tev->reroute minus visible->reroute | -0.031 [-0.051, -0.012] | +4.3 [+3.3, +5.3] | +1913 [+1709, +2127] |
| [transfer] tev->resample(2)->reroute minus strong-only | +0.006 [-0.026, +0.036] | -4.8 [-7.0, -2.8] | +296 [-94, +705] |
| [transfer] tev->resample(2)->reroute minus visible->reroute | -0.034 [-0.055, -0.015] | +4.8 [+3.6, +6.1] | +2406 [+2118, +2706] |
| [transfer] tev->resample(3)->reroute minus strong-only | +0.003 [-0.032, +0.037] | -3.8 [-6.2, -1.5] | +783 [+284, +1319] |
| [transfer] tev->resample(3)->reroute minus visible->reroute | -0.036 [-0.059, -0.015] | +5.8 [+4.3, +7.3] | +2893 [+2494, +3300] |
| [transfer] tev->resample(4)->reroute minus strong-only | +0.001 [-0.037, +0.037] | -2.8 [-5.4, -0.1] | +1248 [+635, +1919] |
| [transfer] tev->resample(4)->reroute minus visible->reroute | -0.039 [-0.063, -0.015] | +6.8 [+5.0, +8.7] | +3359 [+2842, +3886] |
| [transfer] tev->resample(5)->reroute minus strong-only | -0.004 [-0.044, +0.035] | -1.7 [-4.6, +1.3] | +1701 [+975, +2496] |
| [transfer] tev->resample(5)->reroute minus visible->reroute | -0.043 [-0.070, -0.016] | +7.9 [+5.7, +10.1] | +3811 [+3175, +4460] |
| [transfer] llama->reroute minus strong-only | +0.000 [-0.014, +0.017] | +2.1 [+1.2, +3.1] | +1673 [+1412, +1950] |
| [transfer] llama->reroute minus visible->reroute | -0.039 [-0.063, -0.015] | +11.7 [+9.9, +13.9] | +3783 [+3377, +4214] |
| [transfer] selfconf->reroute minus strong-only | -0.006 [-0.014, +0.003] | -0.7 [-1.9, +0.4] | -38 [-263, +157] |
| [transfer] selfconf->reroute minus visible->reroute | -0.045 [-0.077, -0.016] | +8.9 [+7.7, +10.1] | +2072 [+1849, +2300] |
| [transfer] vis&tev->reroute minus strong-only | +0.033 [+0.013, +0.056] | -4.7 [-6.5, -3.1] | -291 [-539, -51] |
| [transfer] vis&tev->reroute minus visible->reroute | -0.006 [-0.022, +0.010] | +4.9 [+4.1, +5.7] | +1819 [+1640, +2010] |
| [transfer] vis&llama->reroute minus strong-only | +0.011 [-0.002, +0.027] | +2.1 [+1.2, +3.0] | +1333 [+1111, +1573] |
| [transfer] vis&llama->reroute minus visible->reroute | -0.028 [-0.051, -0.006] | +11.7 [+9.9, +13.9] | +3444 [+3029, +3889] |
| [transfer] vis&selfconf->reroute minus strong-only | +0.004 [-0.001, +0.010] | -0.3 [-1.5, +0.7] | +48 [-178, +239] |
| [transfer] vis&selfconf->reroute minus visible->reroute | -0.036 [-0.068, -0.007] | +9.3 [+8.2, +10.4] | +2159 [+1958, +2373] |
| [transfer] tev&sc@frozen->reroute minus strong-only | -0.002 [-0.008, +0.003] | +1.4 [+0.2, +2.4] | +1365 [+1172, +1550] |
| [transfer] tev&sc@frozen->reroute minus visible->reroute | -0.041 [-0.073, -0.012] | +10.9 [+9.8, +12.2] | +3475 [+3244, +3730] |
| [transfer] tev|sc@frozen->reroute minus strong-only | +0.005 [-0.020, +0.031] | -5.8 [-7.7, -4.1] | -288 [-578, -7] |
| [transfer] tev|sc@frozen->reroute minus visible->reroute | -0.034 [-0.055, -0.016] | +3.8 [+2.9, +4.7] | +1823 [+1624, +2031] |
| [recal] tev->reroute minus strong-only | +0.009 [-0.015, +0.034] | -5.3 [-7.2, -3.7] | -197 [-484, +82] |
| [recal] tev->reroute minus visible->reroute | -0.031 [-0.051, -0.012] | +4.3 [+3.3, +5.3] | +1913 [+1709, +2127] |
| [recal] tev->resample(2)->reroute minus strong-only | +0.006 [-0.026, +0.036] | -4.8 [-7.0, -2.8] | +296 [-94, +705] |
| [recal] tev->resample(2)->reroute minus visible->reroute | -0.034 [-0.055, -0.015] | +4.8 [+3.6, +6.1] | +2406 [+2118, +2706] |
| [recal] tev->resample(3)->reroute minus strong-only | +0.003 [-0.032, +0.037] | -3.8 [-6.2, -1.5] | +783 [+284, +1319] |
| [recal] tev->resample(3)->reroute minus visible->reroute | -0.036 [-0.059, -0.015] | +5.8 [+4.3, +7.3] | +2893 [+2494, +3300] |
| [recal] tev->resample(4)->reroute minus strong-only | +0.001 [-0.037, +0.037] | -2.8 [-5.4, -0.1] | +1248 [+635, +1919] |
| [recal] tev->resample(4)->reroute minus visible->reroute | -0.039 [-0.063, -0.015] | +6.8 [+5.0, +8.7] | +3359 [+2842, +3886] |
| [recal] tev->resample(5)->reroute minus strong-only | -0.004 [-0.044, +0.035] | -1.7 [-4.6, +1.3] | +1701 [+975, +2496] |
| [recal] tev->resample(5)->reroute minus visible->reroute | -0.043 [-0.070, -0.016] | +7.9 [+5.7, +10.1] | +3811 [+3175, +4460] |
| [recal] llama->reroute minus strong-only | +0.000 [-0.014, +0.017] | +2.1 [+1.2, +3.1] | +1673 [+1412, +1950] |
| [recal] llama->reroute minus visible->reroute | -0.039 [-0.063, -0.015] | +11.7 [+9.9, +13.9] | +3783 [+3377, +4214] |
| [recal] selfconf->reroute minus strong-only | -0.006 [-0.014, +0.003] | -0.7 [-1.9, +0.4] | -38 [-263, +157] |
| [recal] selfconf->reroute minus visible->reroute | -0.045 [-0.077, -0.016] | +8.9 [+7.7, +10.1] | +2072 [+1849, +2300] |
| [recal] vis&tev->reroute minus strong-only | +0.039 [+0.010, +0.070] | -8.4 [-10.1, -6.9] | -1138 [-1336, -954] |
| [recal] vis&tev->reroute minus visible->reroute | +0.000 [+0.000, +0.000] | +1.2 [+1.1, +1.3] | +972 [+873, +1071] |
| [recal] vis&llama->reroute minus strong-only | +0.039 [+0.010, +0.070] | -8.4 [-10.0, -7.0] | -917 [-1086, -755] |
| [recal] vis&llama->reroute minus visible->reroute | +0.000 [+0.000, +0.000] | +1.2 [+1.0, +1.3] | +1193 [+1053, +1334] |
| [recal] vis&selfconf->reroute minus strong-only | +0.039 [+0.010, +0.070] | -9.6 [-11.3, -8.0] | -2110 [-2382, -1853] |
| [recal] vis&selfconf->reroute minus visible->reroute | +0.000 [+0.000, +0.000] | +0.0 [+0.0, +0.0] | +0 [+0, +0] |
| [recal] tev&sc->reroute minus strong-only | +0.009 [-0.014, +0.034] | -4.8 [-6.7, -3.2] | -21 [-302, +264] |
| [recal] tev&sc->reroute minus visible->reroute | -0.031 [-0.054, -0.009] | +4.8 [+3.9, +5.7] | +2090 [+1897, +2292] |
| [recal] tev|sc->reroute minus strong-only | +0.004 [-0.015, +0.022] | -2.8 [-4.4, -1.3] | +444 [+165, +703] |
| [recal] tev|sc->reroute minus visible->reroute | -0.036 [-0.063, -0.010] | +6.8 [+5.9, +7.8] | +2555 [+2350, +2763] |
| cascade 3B->7B->14B gate visible minus strong-only | +0.057 [+0.022, +0.094] | -10.5 [-12.3, -8.7] | -2237 [-2515, -1953] |
| cascade 3B->7B->14B gate visible minus visible->reroute | +0.018 [+0.005, +0.033] | -0.9 [-1.4, -0.3] | -127 [-220, -34] |
| cascade 3B->7B->14B gate tev [transfer] minus strong-only | +0.010 [-0.018, +0.040] | -3.1 [-5.3, -0.9] | +686 [+261, +1140] |
| cascade 3B->7B->14B gate tev [transfer] minus visible->reroute | -0.029 [-0.049, -0.011] | +6.5 [+5.2, +8.0] | +2796 [+2477, +3152] |
| cascade 3B->7B->14B gate vis&tev [transfer] minus strong-only | +0.041 [+0.014, +0.070] | -2.4 [-4.7, -0.4] | +567 [+193, +950] |
| cascade 3B->7B->14B gate vis&tev [transfer] minus visible->reroute | +0.002 [-0.012, +0.015] | +7.2 [+6.0, +8.5] | +2677 [+2395, +2958] |

## Recalibrated taus (calibration split, pre-registered rule)

- tev: 0.8619849230515471
- llama: 0.4667895416652746
- selfconf: 0.9602630454757016
- vis&tev: 0.015787820863428812
- vis&llama: 0.009642202814064459
- vis&selfconf: 0.6160262074661614
- tev&sc: 0.3684210526315789
- tev|sc: 0.7733918128654971
