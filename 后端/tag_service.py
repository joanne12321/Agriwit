
# tag_service.py - 完整升级版
from flask import Flask, jsonify, request
from flask_cors import CORS  # 添加这一行
from neo4j import GraphDatabase

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})  # 添加这一行，允许跨域访问

# ===== 配置 =====
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "521218fF"
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ===== 接口1：智能推荐标签 =====
@app.route('/api/tags/recommend', methods=['POST'])
def recommend_tags():
    """智能推荐标签"""
    data = request.json
    platform = data.get('platform')
    region = data.get('region')
    product_category = data.get('product_category')
    
    print(f"📦 收到请求：{platform} | {region} | {product_category}")
    
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Platform {name: $platform})-[:HAS_CATEGORY]->(cat)-[:CONTAINS]->(pt:Tag)
            OPTIONAL MATCH (r:Region {name: $region})-[:HAS_KEYWORD]->(rt:CultureTag)
            OPTIONAL MATCH (pc:ProductCategory {name: $product_category})-[:HAS_ATTRIBUTE]->(at:AttributeTag)
            
            RETURN collect(DISTINCT pt.name)[0..8] as platform_tags,
                   collect(DISTINCT rt.name) as region_tags,
                   collect(DISTINCT at.name) as attribute_tags
            LIMIT 1
        """, platform=platform, region=region, product_category=product_category)
        
        record = result.single()
        if record:
            response = {
                "platform_tags": record["platform_tags"],
                "region_tags": record["region_tags"],
                "attribute_tags": record["attribute_tags"]
            }
            print(f"✅ 返回 {len(record['platform_tags'])} 个平台标签")
            return jsonify(response)
    
    print("❌ 查询失败")
    return jsonify({"error": "查询失败"}), 500

# ===== 接口2：获取禁用词 =====
@app.route('/api/forbidden-words', methods=['GET'])
def get_forbidden_words():
    """返回所有禁用词"""
    print("📦 收到请求：获取禁用词")
    
    with driver.session() as session:
        result = session.run("MATCH (fw:ForbiddenWord) RETURN collect(fw.word) as words")
        record = result.single()
        if record:
            print(f"✅ 返回 {len(record['words'])} 个禁用词")
            return jsonify({"words": record["words"]})
    
    return jsonify({"words": []})

# ===== 接口3：获取地域风格 =====
@app.route('/api/region/<region_name>', methods=['GET'])
def get_region_style(region_name):
    """获取地域文案风格指南"""
    print(f"📦 收到请求：获取 {region_name} 的风格")
    
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Region {name: $name})-[:HAS_KEYWORD]->(tag:CultureTag)
            RETURN r.style_guide as style, 
                   r.emotions as emotions,
                   r.areas as areas,
                   collect(tag.name) as keywords
        """, name=region_name)
        
        record = result.single()
        if record:
            print(f"✅ 返回风格指南")
            return jsonify({
                "region": region_name,
                "style_guide": record["style"],
                "emotions": record.get("emotions", ""),
                "areas": record.get("areas", ""),
                "keywords": record["keywords"]
            })
    
    print("❌ 未找到该地域")
    return jsonify({"error": "未找到该地域"}), 404

# ===== 🆕 接口4：获取所有可选标签（详细分类版）=====
@app.route('/api/tags/all', methods=['GET'])
def get_all_tags():
    """
    获取所有标签列表，供用户手动选择（完整详细版）
    
    示例：
    GET /api/tags/all?platform=小红书&region=客家文化区&product_category=生鲜果蔬
    
    返回：
    {
      "platform_tags": [
        {
          "category": "核心品类标签",
          "tags": ["#乡村美食", "#农家特产", ...]
        },
        {
          "category": "场景与情感标签",
          "tags": ["#妈妈的味道", "#童年记忆", ...]
        }
      ],
      "region_info": {
        "name": "客家文化区",
        "areas": "梅州、河源、惠州",
        "keywords": ["#客家山区", ...],
        "emotions": ["古朴", "大山情怀", ...],
        "style_guide": "..."
      },
      "product_attributes": ["#爆汁", "#树上熟", ...],
      "culture_tags": [
        {
          "category": "节气/时令类",
          "tags": ["#不时不食", ...]
        }
      ]
    }
    """
    platform = request.args.get('platform')
    region = request.args.get('region')
    product_category = request.args.get('product_category')
    
    print(f"📋 获取详细标签：{platform} | {region} | {product_category}")
    
    result = {
        "platform_tags": [],
        "region_info": None,
        "product_attributes": [],
        "culture_tags": [],
        "festival_tags": []  
    }
    
    with driver.session() as session:
        # 1. 获取平台标签（按详细分类）
        if platform:
            platform_result = session.run("""
                MATCH (p:Platform {name: $platform})-[:HAS_CATEGORY]->(cat)-[:CONTAINS]->(t:Tag)
                RETURN cat.name as category, collect(t.name) as tags
                ORDER BY cat.name
            """, platform=platform)
            
            for record in platform_result:
                result["platform_tags"].append({
                    "category": record["category"],
                    "tags": record["tags"],
                    "count": len(record["tags"])
                })
        
        # 2. 获取地域完整信息（包含情感词）
        if region:
            region_result = session.run("""
                MATCH (r:Region {name: $region})
                OPTIONAL MATCH (r)-[:HAS_KEYWORD]->(tag:CultureTag)
                RETURN r.name as name,
                       r.areas as areas,
                       r.style_guide as style,
                       r.emotions as emotions,
                       collect(tag.name) as keywords
            """, region=region)
            
            record = region_result.single()
            if record:
                result["region_info"] = {
                    "name": record["name"],
                    "areas": record.get("areas", ""),
                    "keywords": record["keywords"],
                    "emotions": record.get("emotions", "").split(",") if record.get("emotions") else [],
                    "style_guide": record.get("style", "")
                }
        
        # 3. 获取产品属性标签
        if product_category:
            attr_result = session.run("""
                MATCH (pc:ProductCategory {name: $category})-[:HAS_ATTRIBUTE]->(attr:AttributeTag)
                RETURN collect(attr.name) as tags
            """, category=product_category)
            
            record = attr_result.single()
            if record:
                result["product_attributes"] = record["tags"]
        
         # 4. 修改后的通用文化标签获取逻辑
        culture_result = session.run("""
            MATCH (ct:CultureType)-[:INCLUDES]->(tag:CultureTag)
            RETURN ct.name as category, collect(tag.name) as tags
        """)
        
        for record in culture_result:
            cat_name = record["category"]
            tags = record["tags"]
            
            # 如果类别是节日，单独放进 festival_tags
            if "节日" in cat_name or "时令" in cat_name:
                result["festival_tags"].extend(tags)
            
            result["culture_tags"].append({
                "category": cat_name,
                "tags": tags,
                "count": len(tags)
            })
            
    return jsonify(result)
        
    
    # 统计标签总数
    total_platform = sum(cat['count'] for cat in result['platform_tags'])
    total_region = len(result['region_info']['keywords']) if result['region_info'] else 0
    total_product = len(result['product_attributes'])
    total_culture = sum(cat['count'] for cat in result['culture_tags'])
    
    print(f"✅ 返回标签统计：")
    print(f"   平台标签：{total_platform}个（{len(result['platform_tags'])}个分类）")
    print(f"   地域标签：{total_region}个")
    print(f"   产品属性：{total_product}个")
    print(f"   文化标签：{total_culture}个（{len(result['culture_tags'])}个分类）")
    
    return jsonify(result)

# ===== 启动服务 =====
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 标签服务已启动（升级版）！")
    print("="*70)
    print("📍 地址：http://localhost:5000")
    print("\n💡 接口列表：")
    print("  1. POST /api/tags/recommend        - 智能推荐标签")
    print("  2. GET  /api/forbidden-words       - 获取禁用词")
    print("  3. GET  /api/region/<name>         - 获取地域风格")
    print("  4. GET  /api/tags/all              - 获取所有可选标签（详细版）")
    print("\n💡 按 Ctrl+C 停止服务")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5002, host='0.0.0.0')
