"""
Build data/contrast/candidates_clean/古风.json  (contrast set: modern "ancient-style" Chinese pop, 古风).

Every candidate ID comes from a live, logged search with src/secaiqu/v2/search.py
(AQ_COLLECTION=data/contrast, region 古风, platform bili). Title, channel, channel_id,
duration and the source query are read back from data/contrast/logs/search_bili.jsonl, so no ID is typed from
memory without a logged hit. Credits (composer, lyricist, year) come from (a) the uploader's description
in the logged hit ("bilibili-desc:<BV>"), (b) WebSearch results ("websearch"), or (c) the curator's knowledge
("knowledge"). Year is the release year (single or album release), not the upload year.

Usage (py312):  python src/contrast/build_gufeng.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data/contrast/logs/search_bili.jsonl"
OUT = ROOT / "data/contrast/candidates_clean/古风.json"

# substyle codes
W, Z, X, O, M = "网络古风", "中国风", "戏腔", "OST", "民族风古风"

# (id, song, composer, lyricist, year, substyle, idiom_region, singer, performance_type, sources, note, tier)
# tier 1 = core, 2 = backup. Order inside a substyle = preference.
D = lambda *a: a
ENTRIES = [
 # ---- 中国风 pop -------------------------------------------------------------------------------------------
 D("BV1tMEy6nEcv","东风破","周杰伦","方文山",2003,Z,"","周杰伦","original",["bilibili-desc:BV1MT4y1n73L","knowledge"],"album 叶惠美; 4K-restored MV re-upload",1),
 D("BV1kt411A7rb","发如雪","周杰伦","方文山",2005,Z,"","周杰伦","original",["bilibili-desc:BV1MFH76XErp"],"album 十一月的萧邦 (2005-11-11); MV re-upload",1),
 D("BV18v4y1q7mT","菊花台","周杰伦","方文山",2006,Z,"","周杰伦","original",["bilibili-desc:BV1Fk4y1s77V"],"film song 满城尽带黄金甲; album 依然范特西 (2006-09-05); MV re-upload",1),
 D("BV1JB4y1H74o","千里之外","周杰伦","方文山",2006,Z,"","周杰伦 & 费玉清","original",["bilibili-desc:BV12JHq66EDt","knowledge"],"album 依然范特西; duet; MV re-upload",1),
 D("BV1r7411p7R4","青花瓷","周杰伦","方文山",2007,Z,"","周杰伦","original",["bilibili-desc:BV1umHk6oE1w"],"album 我很忙 (2007-11-02); MV re-upload",1),
 D("BV1wL4y1E7mM","兰亭序","周杰伦","方文山",2008,Z,"","周杰伦","original",["bilibili-desc:BV1aruC6iEsX"],"album 魔杰座 (2008-10-15); MV re-upload",1),
 D("BV1HG4y1d7FL","红尘客栈","周杰伦","方文山",2012,Z,"","周杰伦","original",["bilibili-desc:BV1ZpH46ZEMo"],"album 十二新作 (2012-12-28); MV re-upload",1),
 D("BV1R75n6HEST","卷珠帘","LUNA, 彭飞, 捞仔","李姝, LUNA",2014,Z,"","霍尊","original",["websearch:chinanews.com.cn/cul/2014/02-25/5879186.shtml"],"first performed on 中国好歌曲 2014-01; credit order per WebSearch summary, verify before release; Hi-Res re-upload",1),
 D("BV1DU4y1878a","清明雨上","许嵩","许嵩",2009,Z,"","许嵩","original",["bilibili-desc:BV1ps4y1E7oG"],"album 自定义 (2009); MV re-upload",1),
 D("BV1Qi4y1z7Zw","庐州月","许嵩","许嵩",2009,Z,"","许嵩","original",["bilibili-desc:BV1Qi4y1z7Zw"],"first released 2009-12-10 on vaecn, album 寻雾启示 (2010-01); audio re-upload",1),
 D("BV1pN4y1W7Fw","断桥残雪","许嵩","许嵩",2007,Z,"","许嵩","original",["bilibili-desc:BV1pN4y1W7Fw"],"album Vae新歌+精选珍藏合辑 (2007-06-02); audio re-upload",1),
 D("BV1js4y1M7Mj","惊鸿一面","许嵩","许嵩",2014,Z,"","许嵩 & 黄龄","original",["bilibili-desc:BV1js4y1M7Mj"],"album 不如吃茶去 (2014); duet; audio re-upload",1),
 D("BV1gc411n7vC","半城烟沙","许嵩","许嵩",2010,Z,"","许嵩","original",["bilibili-desc:BV1gc411n7vC"],"theme of game 天龙八部2 (2010); audio re-upload",1),
 D("BV1Dq4y127RY","曹操","林俊杰","林秋离",2006,Z,"","林俊杰","original",["bilibili-desc:BV1kN411M73n"],"album 曹操 (2006-02-17); MV re-upload",1),
 D("BV1jTxxesEMY","醉赤壁","林俊杰","方文山",2008,Z,"","林俊杰","original",["bilibili-desc:BV1jTxxesEMY"],"album JJ陆 (2008-10-18); audio re-upload",1),
 D("BV12XHk6pEft","痒","孟楠","孟楠",2007,Z,"","黄龄","original",["bilibili-desc:BV12XHk6pEft"],"album 痒 (2007-03); erhu/xiao/pipa arrangement; MV re-upload",1),
 D("BV1q64y1d7Ee","万疆","刘颜嘉","李姝",2021,Z,"","李玉刚","original",["bilibili-desc:BV1Zu4y147u5"],"single 2021-05-04; singer's own upload (李玉刚)",1),
 D("BV1De4y1N7Bz","花开忘忧","钱雷","唐恬",2022,Z,"","周深","original",["bilibili-desc:BV1De4y1N7Bz"],"single 2022-09-10; audio re-upload",1),
 D("BV1ZepX6uEqE","不死鸟","霍尊","甘世佳, 霍尊",2020,Z,"","霍尊","original",["bilibili-desc:BV1ZepX6uEqE"],"album 归一 (2020-11-02); audio re-upload; mainstream pop with phoenix imagery",1),
 D("BV1K4411K7Yh","月满弦","刘珂矣, 百慕三石","刘珂矣",2019,Z,"","刘珂矣","original",["bilibili-desc:BV1K4411K7Yh"],"禅意中国风; singer's own upload; MV",1),
 D("BV16p411f7sq","半壶纱","刘珂矣, 百慕三石","刘珂矣, 百慕三石",2016,Z,"","刘珂矣","original",["bilibili-desc:BV16p411f7sq","bilibili-desc:BV16hMuzaEN7"],"album 半壶纱 (2016-01-05); singer's own upload; MV",1),
 D("BV1qz4y1g75R","天下","刘吉宁","周毅",2008,Z,"","张杰","original",["bilibili-desc:BV1qz4y1g75R"],"album 明天过后 (2008-09-15); audio re-upload",1),
 D("BV1Sy4y1R75J","江南","林俊杰","林秋离",2004,Z,"Jiangsu-Zhejiang_Plain (lyric imagery only)","林俊杰","original",["bilibili-desc:BV1Sy4y1R75J"],"album 第二天堂 (2004-06-04); year before 2005; audio re-upload",2),
 D("BV1ZL411g7tj","霍元甲","周杰伦","方文山",2006,O,"","周杰伦","original",["knowledge"],"film song 霍元甲; album 依然范特西; MV re-upload",2),
 D("BV1jwhoeoEvb","烟花易冷","周杰伦","方文山",2010,Z,"","周杰伦","original",["bilibili-desc:BV1X1H26CEJU"],"album 跨时代 (2010-05-18); re-upload",2),
 D("BV1NpRPBxEyt","天涯过客","周杰伦","方文山",2014,Z,"","周杰伦","original",["bilibili-desc:BV117Hd69Een"],"album 哎呦，不错哦 (2014-12-26); 4K-restored MV re-upload",2),
  # ---- 戏腔 / opera-coloured -----------------------------------------------------------------------------------
 D("BV14a4y1y7JC","赤伶","李建衡","清彦",2018,X,"Peking opera (京剧) vocal style","HITA","original",["bilibili-desc:BV1eBBXYGE6v"],"single 2018-09-27; audio re-upload",1),
 D("BV19ri8BYE4u","在梅边","王力宏","阿信",2005,X,"Kunqu / Peking opera elements (牡丹亭)","王力宏","original",["bilibili-desc:BV1Xa411s7Md"],"album 盖世英雄 (2005-12-30); MV re-upload",1),
 D("BV1iW411V7PH","承君","泠泠","瞳荧",2018,X,"Peking opera (花脸 spoken part)","Aki阿杰","original",["bilibili-desc:BV1iW411V7PH"],"singer's own upload; 352 s; V-singer original by 言和 x 洛天依, human version by Aki阿杰",1),
 D("BV1ks4y1G7YV","谪仙","王中易","王莹",2023,X,"","平生不晚","official_cover",["bilibili-desc:BV1ks4y1G7YV","bilibili-desc:BV1GR7UzQEQX"],"authorised 戏腔 version (2023) of the original sung by 叶里 (伊格赛听); 3 min",1),
 D("BV1hh411B7yj","吾与子","金丝草 lvy, 李扶澜","惊竹娇",2021,X,"Peking opera (戏腔)","李扶澜","original",["bilibili-desc:BV1hh411B7yj"],"国风原创; year = upload year (no release date in description)",1),
 D("BV17s411h7F3","戏中人","槿生","不白的白菜",2017,X,"Peking opera (霸王别姬)","上古呐 & 伯虎","original",["bilibili-desc:BV17s411h7F3"],"year = upload year; uploader is a re-uploader",1),
 D("BV1Cz4y1973t","新霸王别姬","孙毅然","未见钗头凤",2020,X,"Peking opera (京剧)","阿杰 (CV)","original",["bilibili-desc:BV1Cz4y1973t"],"game 食物语 character song, official PV; year = upload year",1),
 # ---- OST ------------------------------------------------------------------------------------------------------
 D("BV1So4y1P78w","逍遥叹","陈宇任 (Funck)","陈宇任 (Funck)",2005,O,"","胡歌","original",["bilibili-desc:BV1Tf81zvEfn"],"TV drama 仙剑奇侠传 (OST 2005-01-25); audio re-upload",1),
 D("BV1Go4y1j78f","红颜旧","赵佳霖","袁亮",2015,O,"","刘涛","original",["bilibili-desc:BV1Go4y1j78f"],"TV drama 琅琊榜 (2015-10-26); audio re-upload",1),
 D("BV1oo4y137jx","知否知否","刘炫豆","李清照, 张靖怡",2018,O,"","胡夏 & 郁可唯","original",["bilibili-desc:BV1oo4y137jx","websearch"],"TV drama 知否知否应是绿肥红瘦 (2018); audio re-upload",1),
 D("BV1HXUeBREik","凉凉","谭旋","刘畅",2017,O,"","杨宗纬 & 张碧晨","original",["bilibili-desc:BV1HXUeBREik"],"TV drama 三生三世十里桃花 (single 2017-01-09); audio re-upload",1),
 D("BV1w84y1f7pY","不染","简弘亦","海雷",2018,O,"","毛不易","original",["bilibili-desc:BV1w84y1f7pY"],"TV drama 香蜜沉沉烬如霜 (2018); year = drama year; produced by 萨顶顶; audio re-upload",1),
 D("BV1mM411Y77i","大鱼","钱雷","尹约",2016,O,"","周深","original",["bilibili-desc:BV1mM411Y77i","websearch"],"film 大鱼海棠 theme (2016-05-20); audio re-upload",1),
 D("BV157y5BVE64","画心","藤原育郎","陈少琪",2008,O,"","张靓颖","original",["bilibili-desc:BV1ftKBzuEHN","websearch"],"film 画皮 theme (2008-10-20); audio re-upload",1),
 D("BV1JL411B7oL","典狱司","和汇慧","江淮沿岸",2016,O,"","音频怪物","original",["bilibili-desc:BV1JL411B7oL"],"TV drama 老九门 closing song; year = drama year (2016); audio re-upload",1),
 D("BV16tVB6yEMR","劫","和汇慧, 王梓同","王明毓",2020,O,"","音频怪物","original",["bilibili-desc:BV16tVB6yEMR"],"TV drama 琉璃 (OST 2020-08-14); audio re-upload",1),
 D("BV1tZ4y1v7gx","梦华","代岳东","代岳东, 闫立严",2022,O,"","刘宇宁","original",["bilibili-desc:BV1tZ4y1v7gx"],"TV drama 梦华录 opening (2022-06-02); re-upload",1),
 D("BV18V411H7Ef","缘灭","郑冰冰","马程程",2021,O,"","双笙","original",["bilibili-desc:BV18V411H7Ef"],"web drama 山河令 insert song; year = drama year; audio re-upload",1),
 D("BV1EG41137Xw","天涯明月刀","小虫","小虫",2012,O,"","钟汉良","original",["bilibili-desc:BV1EG41137Xw"],"TV drama 天涯明月刀 theme (2012-07-05)",1),
 D("BV1ty4y1L78S","美丽的神话","崔浚荣","王中言",2005,O,"Xinjiang / Silk Road colour (lyric)","成龙 & 金喜善","original",["bilibili-desc:BV11D4HeaEw3"],"film 神话 theme (2005); MV re-upload",1),
 D("BV1wd4y1e7vw","雪落下的声音","陆虎","于正",2018,O,"","陆虎","original",["bilibili-desc:BV1wd4y1e7vw"],"TV drama 延禧攻略 (single 2018-07-23); audio re-upload",1),
 D("BV12B4y1B7DL","如愿","钱雷","唐恬",2021,O,"","王菲","original",["bilibili-desc:BV12B4y1B7DL"],"film 我和我的父辈 theme (2021-09-25); official-MV re-upload",1),
 D("BV1DP411o7P6","星河叹","关大洲","王梓嫣",2022,O,"","黄龄","original",["bilibili-desc:BV1DP411o7P6"],"TV drama 星汉灿烂 (2022-07-20); audio re-upload",1),
 D("BV1gx4y1A7pn","诀爱","姜楠, 陈恬","姜楠, 陈恬",2022,O,"","詹雯婷","original",["bilibili-desc:BV1gx4y1A7pn"],"TV drama 苍兰诀 (single 2022-08-14); audio re-upload",1),
 D("BV1oV411n7ZQ","光的方向","金大洲","萨吉",2021,O,"","张碧晨","original",["bilibili-desc:BV1oV411n7ZQ"],"TV drama 长歌行 opening; year = drama year; official MV (QQ音乐)",1),
 D("BV1pW4y1h75V","道不得经","朱剑, 汤汤","冥凰",2022,O,"","朱剑 & 喵☆酱","original",["bilibili-desc:BV1pW4y1h75V"],"game 纸嫁衣4 theme; year = upload year; official game channel",1),
 D("BV1J7411q7wR","红颜","胡彦斌","林文炫",2004,O,"","胡彦斌","original",["bilibili-desc:BV1Yb411v7E6"],"TV drama 荆轲传奇 theme; album MUSIC混合体 (2004-08-25); year before 2005; MV re-upload",1),
 D("BV1HW4y1c7Ss","剑伤","陆虎","陆虎",2014,O,"","李易峰","original",["bilibili-desc:BV1HW4y1c7Ss"],"TV drama 古剑奇谭 theme; year = drama year (2014); audio re-upload",1),
 D("BV13r4y1o7VR","人世太匆忙","严艺丹","严艺丹",2023,O,"","严艺丹","original",["bilibili-desc:BV13r4y1o7VR"],"TV drama 莲花楼 closing; year = drama year; MV re-upload",1),
 D("BV1YheXzrEm9","归舟","Jannik","沃特艾文儿",2025,M,"Northwest_Plateau (Hexi corridor, game region 河西)","谭晶","original",["bilibili-desc:BV1YheXzrEm9"],"game 燕云十六声 concept song; singer's own upload; year = upload year (2025)",1),
 # ---- 网络古风 ---------------------------------------------------------------------------------------------------
 D("BV1ZL411i7YQ","牵丝戏","银临","Vagary",2015,W,"","银临 & Aki阿杰","original",["bilibili-desc:BV1ZL411i7YQ","bilibili-desc:BV1Q34y1P7Ef"],"single 2015; audio re-upload",1),
 D("BV1fh411N7Qx","锦鲤抄","银临","慕清明",2013,W,"","银临 & 云の泣","original",["bilibili-desc:BV1L33R6CEEx"],"released 2013-04-09; album 腐草为萤 (2013-08)",1),
 D("BV1fs411y7dW","不老梦","银临","慕清明",2016,W,"","银临","original",["bilibili-desc:BV1fs411y7dW"],"singer's own upload; year = first upload (2016); album 蚍蜉渡海 compiles it (2017)",1),
 D("BV1ss4y1y7WE","棠梨煎雪","灰原穷, 银临","商连",2013,W,"","银临","original",["bilibili-desc:BV17e411K7bD","websearch"],"album 腐草为萤 (2013-08-23); audio re-upload",1),
 D("BV1LB42167MR","流光记","潮汐-tide, 银临","迟意",2018,W,"","银临","original",["bilibili-desc:BV1LB42167MR","bilibili-desc:BV1A441137JP"],"released 2018-10-02; audio re-upload",1),
 D("BV1F4411E7T8","金陵谣","Tureleon","颀鞍",2019,W,"Jiangsu-Zhejiang_Plain (Nanjing city theme)","银临","original",["bilibili-desc:BV1F4411E7T8"],"国风堂 city series; singer's own upload; year = upload year",1),
 D("BV1oW411T733","红昭愿","殇小谨","偏生梓归 (荒唐客)",2017,W,"","音阙诗听","original",["bilibili-desc:BV1oW411T733","bilibili-desc:BV1pJsgz2EqH"],"single 2017-01; group's own upload",1),
 D("BV1vSMizPEqM","芒种","殇小谨","假寐",2019,W,"","音阙诗听 & 赵方婧","original",["bilibili-desc:BV1vSMizPEqM"],"single 2019-06-06; audio re-upload",1),
 D("BV1gJ411m7Cb","清明梦","殇小谨","假寐",2019,W,"","李佳思 & 音阙诗听","original",["bilibili-desc:BV1gJ411m7Cb"],"group's own upload; year = upload year",1),
 D("BV1xy4y1S7k6","闭月","殇小谨","偏生梓归",2020,W,"","赵方婧 & 音阙诗听","original",["bilibili-desc:BV1xy4y1S7k6"],"group's own upload; year = upload year",1),
 D("BV1zt411m7Ne","盗将行","花粥","姬霄",2018,W,"","花粥 & 马雨阳","original",["bilibili-desc:BV1vt41197cK","bilibili-desc:BV1sK421v7Te"],"album 粥请客(二) (2018-06-19); audio re-upload",1),
 D("BV1jh4y1R75M","世间美好与你环环相扣","柏松","尹初七",2019,W,"","柏松","original",["bilibili-desc:BV1jh4y1R75M"],"album 听闻余生 (2019); audio re-upload",1),
 D("BV1UJ411r7e3","下山","朱斌语","朱斌语",2019,W,"","要不要买菜","original",["bilibili-desc:BV1La8rzqErH","websearch"],"year per WebSearch (article of 2020: 'released last year'); MV re-upload",1),
 D("BV1ZyqhBVEYP","西楼别序","肖腾","峦无眠",2021,W,"","尹昔眠 & 小田音乐社","original",["bilibili-desc:BV1ZyqhBVEYP"],"single/album 2021-01-18; audio re-upload",1),
 D("BV1Ka4y1S7at","不谓侠","潮汐-tide","迟意",2017,W,"","萧忆情Alex","original",["bilibili-desc:BV1Ka4y1S7at"],"album 萧音弥漫 (2017-08-02); audio re-upload",1),
 D("BV1MQR3BSEP2","长安姑娘","谭诺龙","谭诺龙",2020,W,"Northwest_Plateau (Chang'an city theme)","李常超 (Lao乾妈)","original",["bilibili-desc:BV1MQR3BSEP2"],"released 2020-03-28; audio re-upload",1),
 D("BV13S411w74o","春庭雪","爆款","清彦",2020,W,"","等什么君 (邓寓君)","original",["bilibili-desc:BV13S411w74o"],"single 2020-07-11; audio re-upload",1),
 D("BV1fx411A7hz","权御天下","乌龟Sui","ST",2015,W,"","洛天依 (Vocaloid)","original",["bilibili-desc:BV1FwuyzAEsw"],"synthetic singer (洛天依); composer's own upload; no human lead vocal",1),
 D("BV1Mx411Q7hD","大风起兮","李建衡","择荇",2017,W,"","Aki阿杰","original",["bilibili-desc:BV1Mx411Q7hD"],"心时纪 国风音乐会 new song; singer's own upload; year = upload year",1),
 D("BV1CD4y197Lk","青山无恙","西瓜JUN","清彦",2020,W,"","西瓜JUN","original",["bilibili-desc:BV1CD4y197Lk"],"singer's own upload",1),
 D("BV1Ks411L7x5","可以可以","于海航","冉语优",2018,W,"","西瓜JUN","original",["bilibili-desc:BV1Ks411L7x5"],"singer's own upload; year = upload year",1),
 D("BV1us411k7qa","长生诀","西瓜JUN","逸生",2016,W,"","西瓜JUN","original",["bilibili-desc:BV1us411k7qa"],"singer's own upload; year = upload year; 191 s",1),
 D("BV1bW411L7jR","适居山","莫卿","风斯",2018,W,"","HITA","original",["bilibili-desc:BV1bW411L7jR"],"year = upload year; uploader is a fan channel",1),
 D("BV1hjtqz5EXn","一笑江湖","祝何","祝何",2020,W,"","闻人听書","original",["bilibili-desc:BV1JQWtzREq3"],"single 2020-02-19; audio re-upload",1),
 D("BV1rL411M7Yt","清平乐","Zoey","李煜",2021,W,"","Aki阿杰","original",["bilibili-desc:BV1rL411M7Yt"],"game 逆水寒 music contest; producer 银临; official game channel; 155 s; year = upload year",1),
 D("BV1Ay37ziEbt","关山酒","乐金震","Yoki",2018,W,"","小魂","original",["bilibili-desc:BV1Ay37ziEbt","bilibili-desc:BV1o4411C7P8"],"first released 2018-12-31 on 5sing, single 2019-09-03; audio re-upload",2),
 D("BV1TG411e7j1","琵琶行","徒有琴","白居易",2017,W,"","奇然 & 沈谧仁","original",["bilibili-desc:BV1TG411e7j1","bilibili-desc:BV1Rx54znE7k"],"Tang poem set to music; year 2017 inferred from uploader post '发行8年后' (2025), re-arranged 2019-07-05 - verify",2),
 D("BV1Wy421v7ih","九万字","宇恒, 黄诗扶","左木修",2019,W,"","黄诗扶","original",["bilibili-desc:BV1Wy421v7ih","websearch"],"year per album 人间不值得 (2019-01); credits from uploader description - verify",2),
 D("BV1AfosYfEGJ","烟雨楼阁未有雪","瑾仪","十二兄",2025,W,"","闻人听書","original",["bilibili-desc:BV1AfosYfEGJ"],"singer's own upload; year = upload year (2025)",2),
 D("BV1P1421q7nh","司南","孙长磊","颀鞍",2024,W,"Northern_Steppe (morin khuur recorded)","贰婶 (蔡翊昇)","original",["bilibili-desc:BV1P1421q7nh"],"中华回响 series; producer 小鱼萝莉; year = upload year",2),
 # ---- 民族风古风 -------------------------------------------------------------------------------------------------
 D("BV1XT4y1w7ZJ","囍","葛东琪","葛东琪",2020,M,"North China wedding suona (唢呐) idiom","葛东琪","original",["bilibili-desc:BV1Y14y1z7RC"],"single 2020-01-21; composer's own upload",1),
 D("BV1px4y1g7yv","落花洞女","解语花","解语花",2023,M,"Miao / Xiangxi folklore (Southwest_Multi-ethnic)","解语花","original",["bilibili-desc:BV1px4y1g7yv"],"国风民俗乐; year = upload year",1),
 D("BV1Vb4y1S7fz","天光","祝歌Merely","祝歌Merely, 青初霁 (苗语词)",2021,M,"Miao (Hmong-language lyrics; Southwest_Multi-ethnic)","三无Marblue & 司南","original",["bilibili-desc:BV1Vb4y1S7fz"],"Miao-language section; singer's own upload; 325 s",1),
 D("BV1BT4y1Z7Ks","天籁贵州","韦侃","刘洪竣, 韦侃",2021,M,"Miao / Dong (Southwest_Multi-ethnic)","潘小燕","original",["bilibili-desc:BV1BT4y1Z7Ks"],"ethnic-style pop, not network 古风 proper; year = upload year of new version",2),
]

KEYS = ["id","song_name","composer","lyricist","year","substyle","idiom_region","singer","performance_type","sources","note","tier"]


def load_hits():
    hits = {}
    for line in LOG.read_text().splitlines():
        r = json.loads(line)
        if r["region"] != "古风":
            continue
        for h in r["hits"]:
            hits.setdefault(h["id"], (h, r["query"]))
    return hits


def main():
    hits = load_hits()
    rows = []
    for e in ENTRIES:
        d = dict(zip(KEYS, e))
        h, q = hits[d["id"]]  # KeyError = id was not returned by a logged search
        assert 90 <= h["duration_s"] <= 420, (d["id"], h["duration_s"])
        srcs = []
        for s in d["sources"]:
            if s.startswith("bilibili-desc:"):
                srcs.append("https://www.bilibili.com/video/" + s.split(":", 1)[1] + " (uploader description)")
            elif s.startswith("websearch:"):
                srcs.append("https://" + s.split(":", 1)[1])
            else:
                srcs.append(s)
        rows.append(dict(rank=0, tier=d["tier"], sub=d["substyle"], rec={
            "platform": "bili", "id": h["id"], "url": h["url"], "title": h["title"], "channel": h["channel"],
            "channel_id": h["channel_id"], "duration_s": h["duration_s"], "song_name": d["song_name"],
            "composer": d["composer"], "lyricist": d["lyricist"], "year": d["year"], "year_kind": "release",
            "substyle": d["substyle"], "idiom_region": d["idiom_region"], "singer": d["singer"],
            "performance_type": d["performance_type"], "sources": srcs, "source_query": q, "note": d["note"]}))
    # order: core round-robin over sub-styles (weighted by group size), then backups
    core = [r for r in rows if r["tier"] == 1]
    back = [r for r in rows if r["tier"] == 2]
    groups = {}
    for r in core:
        groups.setdefault(r["sub"], []).append(r)
    order, n = [], len(core)
    prog = {k: 0 for k in groups}
    while len(order) < n:
        for k, g in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            # take a group's next item when its progress fraction is behind the global one
            if prog[k] < len(g) and prog[k] / len(g) <= len(order) / n + 1e-9:
                order.append(g[prog[k]]); prog[k] += 1
    # core beyond 80 become backups automatically
    ranked = [r["rec"] for r in order]
    final_core = ranked[:80]
    spill = ranked[80:]
    for rec in spill:
        rec["note"] = "backup; " + rec["note"]
    backups = spill + [r["rec"] for r in back]
    for rec in backups:
        if not rec["note"].startswith("backup"):
            rec["note"] = "backup; " + rec["note"]
    cands = final_core + backups
    ids = [c["id"] for c in cands]
    assert len(ids) == len(set(ids))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"region": "古风", "candidates": cands}, ensure_ascii=False, indent=1))
    from collections import Counter
    print(len(final_core), "core +", len(backups), "backup =", len(cands))
    print(Counter(c["substyle"] for c in cands))
    print(sorted(Counter(c["year"] for c in cands).items()))


if __name__ == "__main__":
    main()
