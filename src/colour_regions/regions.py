"""
The 15 colour regions (色彩区) of the Colour Regions corpus: Chinese names, English names used in the paper,
short codes, Han / minority type, and the main provinces or areas (for tables and maps).

Order: north → south for Han regions, then the four minority song areas.
"""

REGIONS = [
    # code, Chinese name, English name, type, main provinces / areas
    ("NEP", "东北部平原", "Northeast Plain", "Han", "Shandong, Hebei, Tianjin, Beijing, Liaoning, Jilin, Heilongjiang"),
    ("NWP", "西北部高原", "Northwest Plateau", "Han", "Shaanxi, Shanxi, Gansu, Ningxia, Qinghai (east)"),
    ("JH", "江淮", "Jiang–Huai", "Han", "northern Jiangsu, Anhui"),
    ("JZP", "江浙平原", "Jiangsu–Zhejiang Plain", "Han", "southern Jiangsu, Shanghai, Zhejiang"),
    ("JHN", "江汉", "Jiang–Han", "Han", "Hubei, southern Henan"),
    ("XIA", "湘", "Xiang", "Han", "Hunan"),
    ("GAN", "赣", "Gan", "Han", "Jiangxi"),
    ("MT", "闽台", "Min–Tai", "Han", "Fujian, Taiwan"),
    ("YUE", "粤", "Yue", "Han", "Guangdong, Hainan, south-east Guangxi"),
    ("HAK", "客家特区", "Hakka", "Han", "Hakka areas of Guangdong, Fujian, Jiangxi"),
    ("SWP", "西南高原", "Southwest Plateau", "Han", "Sichuan, Chongqing, Guizhou, Yunnan (Han areas)"),
    ("NS", "北方草原文化民歌区", "Northern Steppe", "minority", "Inner Mongolia; Mongol, Daur, Oroqen, Evenki, Hezhen"),
    ("XJ", "新疆民歌区", "Xinjiang", "minority", "Xinjiang; Uyghur, Kazakh, Kyrgyz, Tajik"),
    ("TIB", "藏族民歌区", "Tibetan", "minority", "Tibet, Qinghai, western Sichuan, Gansu; Tibetan"),
    ("SWM", "西南多民族古老原始文化民歌区", "Southwest Multi-ethnic", "minority",
     "Yunnan, Guizhou, Guangxi, Hunan (west); Miao, Dong, Yi, Zhuang, Bai, Hani, …"),
]

CODE = {zh: c for c, zh, *_ in REGIONS}
EN = {zh: en for _, zh, en, *_ in REGIONS}
TYPE = {zh: t for _, zh, _, t, _ in REGIONS}
ORDER = [zh for _, zh, *_ in REGIONS]
