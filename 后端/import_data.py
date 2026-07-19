# import_data_complete.py - 完整版数据导入
from neo4j import GraphDatabase

# ===== 配置 =====
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "521218fF"  # ← 改成你的密码

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

print("\n" + "="*70)
print(" 开始导入完整数据到Neo4j...")
print("="*70 + "\n")

# ========================================
# 第1部分：小红书标签（完整版）
# ========================================
print("📦 【1/7】正在导入小红书标签...")

xiaohongshu_data = {
    "核心品类标签": [
        "乡村美食", "农家特产", "地方特产", "家乡味道",
        "有机蔬菜", "生态水果", "农家手工"
    ],
    "场景与情感标签": [
        "妈妈的味道", "童年记忆", "家乡的味道", "乡村生活",
        "田园生活", "农村美食", "健康饮食", "原生态"
    ],
    "生活方式与种草标签": [
        "好物分享", "美食探店", "懒人食谱", "健康零食",
        "早餐吃什么", "办公室零食", "送礼指南", "伴手礼推荐",
        "我的私藏农产品", "原生态食材", "高颜值礼物"
    ],
    "避坑/测评类标签": [
        "农产品测评", "不踩雷指南"
    ],
    "风格与文化标签": [
        "新农人", "乡村振兴", "非遗美食", "传统手艺", "老品种"
    ]
}

with driver.session() as session:
    session.run("MERGE (p:Platform {code: 'xiaohongshu', name: '小红书'})")
    
    for category, tags in xiaohongshu_data.items():
        session.run("""
            MATCH (p:Platform {code: 'xiaohongshu'})
            MERGE (cat:PlatformCategory {name: $cat, platform: '小红书'})
            MERGE (p)-[:HAS_CATEGORY]->(cat)
        """, cat=category)
        
        for tag in tags:
            session.run("""
                MATCH (cat:PlatformCategory {name: $cat, platform: '小红书'})
                MERGE (t:Tag {name: $tag_name})
                SET t.text = $text
                MERGE (cat)-[:CONTAINS]->(t)
            """, cat=category, tag_name=f"#{tag}", text=tag)
        
        print(f"  ✅ {category}: {len(tags)}个")

# ========================================
# 第2部分：抖音标签（完整版）
# ========================================
print("\n📦 【2/7】正在导入抖音标签...")

douyin_data = {
    "热门流量标签": [
        "三农", "助农", "乡村振兴", "新农人计划", 
        "乡村守护人", "我的乡村生活", "产地现场实拍", "我在大山卖特产"
    ],
    "口号宣传类标签": [
        "每一口都是家乡味"
    ],
    "内容类型标签": [
        "产地直发", "源头好物", "现摘现发", "农家自产",
        "采摘现场", "乡村美食", "农产品"
    ],
    "行为引导与场景标签": [
        "好吃到停不下来", "这是什么神仙味道", "看到就是缘分",
        "支持助农", "家乡特产", "记忆中的味道"
    ],
    "电商转化标签": [
        "抖音商城好物", "抖音助农", "好物推荐"
    ]
}

with driver.session() as session:
    session.run("MERGE (p:Platform {code: 'douyin', name: '抖音'})")
    
    for category, tags in douyin_data.items():
        session.run("""
            MATCH (p:Platform {code: 'douyin'})
            MERGE (cat:PlatformCategory {name: $cat, platform: '抖音'})
            MERGE (p)-[:HAS_CATEGORY]->(cat)
        """, cat=category)
        
        for tag in tags:
            session.run("""
                MATCH (cat:PlatformCategory {name: $cat, platform: '抖音'})
                MERGE (t:Tag {name: $tag_name})
                SET t.text = $text
                MERGE (cat)-[:CONTAINS]->(t)
            """, cat=category, tag_name=f"#{tag}", text=tag)
        
        print(f"  ✅ {category}: {len(tags)}个")

# ========================================
# 第3部分：淘宝关键词（完整版）
# ========================================
print("\n📦 【3/7】正在导入淘宝关键词...")

taobao_data = {
    "属性修饰词": [
        "新鲜现摘", "现挖现发", "产地直供", "顺丰直达", "农家自种",
        "生态种植", "无公害", "老品种", "不打药", "香甜软糯", 
        "脆甜多汁", "粉糯", "小时候的味道"
    ],
    "场景与人群词": [
        "送礼佳品", "年货", "办公室零食", "宝宝辅食", 
        "减肥代餐", "厨房食材", "烧烤食材"
    ],
    "促销与信任词": [
        "包邮", "坏果包赔", "回头客多", "家乡直销", "口碑农产"
    ]
}

with driver.session() as session:
    session.run("MERGE (p:Platform {code: 'taobao', name: '淘宝'})")
    
    for category, keywords in taobao_data.items():
        session.run("""
            MATCH (p:Platform {code: 'taobao'})
            MERGE (cat:PlatformCategory {name: $cat, platform: '淘宝'})
            MERGE (p)-[:HAS_CATEGORY]->(cat)
        """, cat=category)
        
        for kw in keywords:
            session.run("""
                MATCH (cat:PlatformCategory {name: $cat, platform: '淘宝'})
                MERGE (t:Tag {name: $kw})
                SET t.text = $kw
                MERGE (cat)-[:CONTAINS]->(t)
            """, cat=category, kw=kw)
        
        print(f"  ✅ {category}: {len(keywords)}个")

# ========================================
# 第4部分：通用文化/时令库（新增！）
# ========================================
print("\n📦 【4/7】正在导入通用文化/时令库...")

culture_data = {
    "节气/时令类": [
        "不时不食", "春分鲜味", "大暑清欢", "冬至滋补", 
        "抢鲜上市", "时令限定"
    ],
    "非遗/民俗类": [
        "非遗传承", "百年老手艺", "古法炮制", "民俗味道", 
        "非物质文化遗产", "匠心手作"
    ],
    "产地/背书类": [
        "百千万工程", "地标优选", "大山馈赠", "原产地直发", "村长的推荐"
    ]
}

with driver.session() as session:
    for category, tags in culture_data.items():
        # 创建文化类型节点
        session.run("MERGE (ct:CultureType {name: $name})", name=category)
        
        for tag in tags:
            session.run("""
                MATCH (ct:CultureType {name: $category})
                MERGE (tag:CultureTag {name: $tag_name})
                SET tag.text = $text, tag.category = $category
                MERGE (ct)-[:INCLUDES]->(tag)
            """, category=category, tag_name=f"#{tag}", text=tag)
        
        print(f"  ✅ {category}: {len(tags)}个")

# ========================================
# 第5部分：地域文化（完整4个区域）
# ========================================
print("\n📦 【5/7】正在导入地域文化...")

regions = [
 # ── ⼴东省 ──
 {
 "name": "⼴府文化区",
 "areas": "⼴州、佛⼭、肇庆、江⻔、中⼭、珠海、东莞",
 "keywords": ["⼴府好物", "粤味正宗", "省城⼝碑", "⽼⼴味道", "镬⽓⼗⾜"],
 "emotions": ["识⻝", "有镬⽓", "正嘢", "讲究"],
 "style": "强调「讲究」「精细」「⽼字号」，注重品质感，语⽓稳重有信赖感"
 },
 {
 "name": "客家文化区",
 "areas": "梅州、河源、惠州、韶关、清远",
 "keywords": ["客家⼭区", "世界客都", "深⼭好物", "客家纯粹", "⼭泉滋养"],
 "emotions": ["古朴", "⼤⼭情怀", "硬颈精神", "乡愁"],
 "style": "强调「纯净」「原⽣态」「⼤⼭的馈赠」，语⽓朴实有温度，体现客家⼈的勤劳质朴"
 },
 {
 "name": "潮汕文化区",
 "areas": "潮州、汕头、揭阳、汕尾",
 "keywords": ["潮汕优选", "胶⼰⼈", "海⻛滋味", "⼯夫之作", "潮味⼗⾜"],
 "emotions": ["雅致", "挑剔", "求精", "⻝在潮汕"],
 "style": "强调「极度新鲜」「⼯匠精神」「家乡凝聚⼒」，潮汕⼈对⻝材极度讲究，文案要体现专业感"
 },
 {
 "name": "粤⻄/滨海区",
 "areas": "湛江、茂名、阳江、云浮",
 "keywords": ["粤⻄特产", "滨海⻛味", "阳光产地", "海鲜之都", "热带好物"],
 "emotions": ["热情", "豪爽", "阳光", "海⻛"],
 "style": "强调「阳光充⾜」「滨海⻛味」「热带特⾊」，语⽓热情奔放，突出产地阳光⾬⽔充沛的优势"
 },
 # ── 华东地区 ──
 {
 "name": "华东地区",
 "areas": "上海、江苏、浙江、安徽、⼭东、福建",
 "keywords": ["江南好物", "华东特产", "精致⽣活", "品质之选", "东⽅⻛味"],
 "emotions": ["精致", "细腻", "文艺", "品质"],
 "style": "强调「精致」「品质」「江南⻛味」，语⽓细腻优雅，注重产品的精细度和美感"
 },
 # ── 华中地区 ──
 {
 "name": "华中地区",
 "areas": "湖南、湖北、河南、江⻄",
 "keywords": ["中部好物", "湖湘特产", "楚地⻛味", "⽕辣滋味", "中原正味"],
 "emotions": ["⽕辣", "热情", "实在", "地道"],
 "style": "强调「⽕辣」「热情」「地道家乡味」，语⽓豪爽直接，突出产品的浓郁⻛味"
 },
 # ── ⻄南地区 ──
 {
 "name": "⻄南地区",
 "areas": "四川、重庆、云南、贵州",
 "keywords": ["⻄南⼭珍", "云贵⾼原", "⽣态好物", "麻辣鲜⾹", "⾼原特产"],
 "emotions": ["神秘", "⾃然", "豪迈", "⽣态"],
 "style": "强调「⼭珍」「⽣态好物」「⾼原纯净」，语⽓神秘有吸引⼒，突出产地的原⽣态环境"
 },
 # ── ⻄北地区 ──
 {
 "name": "⻄北地区",
 "areas": "陕⻄、⽢肃、宁夏、⻘海、新疆",
 "keywords": ["丝路好物", "⻄北特产", "⼤漠⻛情", "塞上明珠", "⾼原净⼟"],
 "emotions": ["豪迈", "苍凉", "纯净", "厚重"],
 "style": "强调「豪爽」「厚重」「塞上⻛情」，语⽓⼤⽓磅礴，突出⻄北产地⽇照充⾜、昼夜温差⼤的优势"
 },
 # ── 东北地区 ──
 {
 "name": "东北地区",
 "areas": "辽宁、吉林、⿊⻰江",
 "keywords": ["东北特产", "⿊⼟地好物", "关东⻛味", "东北⼤粮仓", "寒地纯净"],
 "emotions": ["实在", "豪爽", "量⼤", "纯粹"],
 "style": "强调「实在量⼤」「东北特⾊」「⿊⼟地」，语⽓豪爽直接，突出东北⿊⼟地孕育的优质农产品"
 },
 # ── 华北地区 ──
 {
 "name": "华北地区",
 "areas": "北京、天津、河北、⼭⻄、内蒙古",
 "keywords": ["华北特产", "京津冀好物", "北⽅⻛味", "传统正味", "燕赵特产"],
 "emotions": ["传统", "厚重", "正宗", "地道"],
 "style": "强调「传统」「地道」「正宗」，语⽓稳重有底⽓，突出产品的历史传承和地域特⾊"
 },
]


with driver.session() as session:
    for region in regions:
        # 创建地域节点
        session.run("""
            MERGE (r:Region {name: $name})
            SET r.areas = $areas, 
                r.style_guide = $style,
                r.emotions = $emotions
        """, name=region["name"], 
             areas=region["areas"], 
             style=region["style"],
             emotions=",".join(region["emotions"]))
        
        # 创建关键词标签
        for keyword in region["keywords"]:
            session.run("""
                MATCH (r:Region {name: $region_name})
                MERGE (tag:CultureTag {name: $tag_name})
                SET tag.text = $text, tag.type = 'region_keyword'
                MERGE (r)-[:HAS_KEYWORD]->(tag)
            """, region_name=region["name"], tag_name=f"#{keyword}", text=keyword)
        
        print(f"  ✅ {region['name']}: {len(region['keywords'])}个关键词")

# ========================================
# 第6部分：产品属性库（完整版）
# ========================================
print("\n📦 【6/7】正在导入产品属性库...")

product_attrs = {
    "生鲜果蔬": ["爆汁", "果径大", "皮薄肉厚", "树上熟", "自然红"],
    "干货坚果": ["脆爽", "自然晾晒", "颗颗饱满", "无添加", "易剥壳"],
    "茶饮冲调": ["头春采摘", "茶香浓郁", "回甘明显", "高山云雾"]
}

with driver.session() as session:
    for category, attrs in product_attrs.items():
        session.run("MERGE (pc:ProductCategory {name: $name})", name=category)
        
        for attr in attrs:
            session.run("""
                MATCH (pc:ProductCategory {name: $category})
                MERGE (tag:AttributeTag {name: $tag_name})
                SET tag.text = $text
                MERGE (pc)-[:HAS_ATTRIBUTE]->(tag)
            """, category=category, tag_name=f"#{attr}", text=attr)
        
        print(f"  ✅ {category}: {len(attrs)}个属性")

# ========================================
# 第7部分：禁用词（完整版）
# ========================================
print("\n📦 【7/7】正在导入禁用词...")

forbidden_words = {
    "绝对化与最高级表述": [
        "最", "最佳", "最具", "最爱", "最赚", "最优", "最优秀", "最好",
        "最大", "最高", "最低", "最便宜", "最流行", "最受欢迎", "最新"
    ],
    "排序与唯一性表述": [
        "第一", "中国第一", "全网第一", "销量第一", "唯一", 
        "独一无二", "No.1", "TOP.1", "仅此一次"
    ],
    "等级与极致表述": [
        "国家级", "全球级", "世界级", "顶级", "顶尖", "尖端",
        "高级", "极品", "极佳", "绝佳", "绝对", "终极", "极致"
    ],
    "首推独家与国字号": [
        "首个", "首选", "独家", "独家配方", "首发", "全网首发",
        "国家免检", "填补国内空白", "中国驰名", "国际品质"
    ],
    "品牌地位与领导者": [
        "大牌", "金牌", "名牌", "王牌", "领袖品牌", "世界领先",
        "领先", "领导者", "巨星", "著名", "至尊", "巅峰", "奢侈", "冠军"
    ],
    "虚假与绝对化承诺": [
        "史无前例", "永久", "万能", "祖传", "特效", "无敌",
        "纯天然", "100%", "高档", "正品", "真皮", "精准"
    ],
    "夸大医疗效果": [
        "补肾", "抗癌", "止咳", "排毒", "降血压", "减肥",
        "根治", "药效", "壮阳", "增高", "治疗", "益气",
        "神效", "奇药", "备孕", "活血化瘀", "清热解毒"
    ],
    "迷信封建类": [
        "转运", "风水", "辟邪", "镇宅", "旺夫", "驱邪",
        "五行", "灵气", "龙脉", "开光", "仙丹", "因果", "功德"
    ]
}

with driver.session() as session:
    for category, words in forbidden_words.items():
        for word in words:
            session.run("""
                MERGE (fw:ForbiddenWord {word: $word})
                SET fw.category = $category
            """, word=word, category=category)
        
        print(f"  ✅ {category}: {len(words)}个")

# ========================================
# 统计
# ========================================
print("\n" + "="*70)
with driver.session() as session:
    # 统计各类节点数量
    stats = {}
    for label in ['Platform', 'PlatformCategory', 'Tag', 'Region', 
                  'CultureTag', 'ProductCategory', 'AttributeTag', 'ForbiddenWord']:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
        stats[label] = result.single()["count"]
    
    total = sum(stats.values())
    
    print("📊 数据导入统计：")
    for label, count in stats.items():
        print(f"  - {label}: {count}个")
    print(f"\n✅ 总计：{total}个节点")

print("="*70)
print("🎉 所有数据导入完成！")
print("="*70 + "\n")

driver.close()
