"""
农产品企业信息登记系统 - 后端 API (完整升级版)
新增：
 - 完整注册信息保存（企业名、地区、电话、⽤户类型）
 - 产品信息独⽴接⼝ /api/product/register
 - UserTrait 模型：对话中学到的产品特征持久化
 - /api/user/{id}/profile 返回完整档案给 ai_service 使⽤
"""
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Enum, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import enum
import os
import uuid
import json
import bcrypt
from pathlib import Path

# ============ 配置 ============
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
DATABASE_URL = "sqlite:///./agriculture.db"
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# ============ 数据库设置 ============
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============ 枚举 ============
class UserType(str, enum.Enum):
    ENTERPRISE = "enterprise"
    INDIVIDUAL = "individual"


class ProductCategory(str, enum.Enum):
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    GRAIN = "grain"
    TEA = "tea"
    OIL = "oil"
    MEAT_EGG = "meat_egg"
    AQUATIC = "aquatic"
    PROCESSED = "processed"
    OTHER = "other"


CATEGORY_LABELS = {
    "vegetable": "⽣鲜果蔬",
    "fruit": "⽔果",
    "grain": "粮油",
    "tea": "茶叶",
    "oil": "⻝⽤油",
    "meat_egg": "⾁蛋禽",
    "aquatic": "⽔产",
    "processed": "加⼯⻝品",
    "other": "其他",
}

# ============ 数据库模型 ============
class User(Base):
    """
    ⽤户表：⼀个账号对应⼀家企业/个⼈农户
    region 保存原始注册地区，如 "⼴东省-梅州市-丙村镇"
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(Enum(UserType), nullable=False, default=UserType.INDIVIDUAL)
    company_name = Column(String, nullable=True)  # 企业名称
    full_name = Column(String, nullable=True)    # 个⼈姓名
    region = Column(String, nullable=False, default="")  # 所在地区
    phone = Column(String, nullable=True)
    registration_step = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="owner", cascade="all, delete-orphan")
    traits = relationship("UserTrait", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    """
    产品表：⼀个⽤户可以有多个产品，is_primary 标记主推产品
    keywords 保存注册时选择的标签（如 ["有机", "送礼", "⾼⼭种植"]）
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # 产品名称
    category = Column(Enum(ProductCategory), nullable=False)
    origin = Column(String, nullable=False)  # 产地（精确到村镇）
    keywords = Column(JSON, nullable=True)   # 特点关键词列表
    description = Column(Text, nullable=True)  # 简短描述
    main_image = Column(String, nullable=True)  # 主图路径
    is_primary = Column(Boolean, default=False)  # 是否为主推产品
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="products")


class UserTrait(Base):
    """
    ⽤户产品特征记忆表：
    从注册关键词 和 对话中动态学习到的特征都存这⾥。
    source = "registration" 表示注册时填写的
    source = "conversation" 表示对话中 AI 提取的
    """
    __tablename__ = "user_traits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_name = Column(String, nullable=True)  # 关联哪个产品（None=全局）
    trait_type = Column(String, nullable=False)   # texture/taste/appearance/usage/story/keyword/description
    trait_value = Column(String, nullable=False)  # 具体特征值，如 "软糯"、"⾹甜"
    source = Column(String, default="conversation")  # registration / conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="traits")


# 创建所有表
Base.metadata.create_all(bind=engine)

# ============ Pydantic 模型 ============
class AuthRegisterRequest(BaseModel):
    username: str
    account: str  # 邮箱
    password: str
    # 图⼀收集的额外字段（前端需要传过来）
    user_type: str = "individual"  # "enterprise" or "individual"
    company_name: Optional[str] = None
    region: str = ""
    phone: Optional[str] = None


class AuthLoginRequest(BaseModel):
    account: str
    password: str


class ProductCreateRequest(BaseModel):
    """注册流程第⼆步：保存产品信息"""
    user_id: int
    name: str
    category: str  # ProductCategory 枚举值字符串
    origin: str
    keywords: List[str] = []
    description: Optional[str] = None
    is_primary: bool = True


class TraitSaveRequest(BaseModel):
    """ai_service 调⽤：保存对话中提取的新特征"""
    user_id: int
    product_name: str
    trait_type: str
    trait_value: str
    source: str = "conversation"


# ============ ⼯具函数 ============
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')[:72]
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False


def get_password_hash(password: str) -> str:
    try:
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"密码加密错误: {e}")
        return bcrypt.hashpw(
            password.encode('utf-8')[:50], bcrypt.gensalt()
        ).decode('utf-8')


def create_access_token(data: dict):
    from jose import jwt
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ FastAPI 应⽤ ============
app = FastAPI(title="农产品企业信息登记系统 v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源，错误响应也能带CORS头
    allow_credentials=False,  # ⽤ * 时必须设为 False
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 路由 ============
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "time": datetime.utcnow().isoformat()}


# ---------- 注册/登录 ----------
@app.post("/api/auth/register")
async def auth_register(data: AuthRegisterRequest, db: Session = Depends(get_db)):
    """
    注册接⼝（图⼀：企业信息登记第⼀步）
    保存：邮箱、密码、⽤户类型、企业名、地区、电话
    """
    print(f" 注册请求: {data.account} | 类型:{data.user_type} | 地区:{data.region}")

    existing = db.query(User).filter(User.email == data.account).first()
    if existing:
        return JSONResponse(status_code=400, content={"detail": "该邮箱已被注册"})

    hashed_password = get_password_hash(data.password)
    user = User(
        email=data.account,
        hashed_password=hashed_password,
        user_type=UserType.ENTERPRISE if data.user_type == "enterprise" else UserType.INDIVIDUAL,
        company_name=data.company_name,
        full_name=data.username,
        region=data.region,
        phone=data.phone,
        registration_step=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": user.id})
    print(f" 注册成功: user_id={user.id}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": data.username,
        "user_id": user.id,
        "message": "注册成功，请继续填写产品信息"
    }


@app.post("/api/auth/login")
async def auth_login(data: AuthLoginRequest, db: Session = Depends(get_db)):
    """登录接⼝"""
    print(f" 登录请求: {data.account}")

    user = db.query(User).filter(User.email == data.account).first()
    if not user or not verify_password(data.password, user.hashed_password):
        return JSONResponse(status_code=401, content={"detail": "邮箱或密码错误"})

    if not user.is_active:
        return JSONResponse(status_code=403, content={"detail": "账号已被禁⽤"})

    access_token = create_access_token({"sub": user.id})
    username = user.full_name or user.company_name or "⽤户"
    print(f" 登录成功: {username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": username,
        "user_id": user.id,
        "registration_step": user.registration_step
    }


# ---------- 产品注册（图⼆：第⼆步）----------
@app.post("/api/product/register")
async def register_product(data: ProductCreateRequest, db: Session = Depends(get_db)):
    """
    注册流程第⼆步：保存产品信息（图⼆的表单）
    注册时填写的关键词会同步存⼊ UserTrait 表，供 AI ⽣成时使⽤
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        return JSONResponse(status_code=404, content={"detail": "⽤户不存在"})

    # 如果设为主推产品，先取消其他产品的主推标记
    if data.is_primary:
        db.query(Product).filter(Product.user_id == data.user_id).update({"is_primary": False})

    # 解析产品类别
    try:
        cat = ProductCategory(data.category)
    except ValueError:
        cat = ProductCategory.OTHER

    product = Product(
        user_id=data.user_id,
        name=data.name,
        category=cat,
        origin=data.origin,
        keywords=data.keywords,
        description=data.description,
        is_primary=data.is_primary
    )
    db.add(product)

    # 关键：把注册时的关键词同步存⼊ UserTrait，让 AI ⽣成时能直接⽤
    for kw in data.keywords:
        trait = UserTrait(
            user_id=data.user_id,
            product_name=data.name,
            trait_type="keyword",
            trait_value=kw,
            source="registration"
        )
        db.add(trait)

    # 描述也存为特征
    if data.description:
        trait = UserTrait(
            user_id=data.user_id,
            product_name=data.name,
            trait_type="description",
            trait_value=data.description,
            source="registration"
        )
        db.add(trait)

    # 产地作为特征
    if data.origin:
        trait = UserTrait(
            user_id=data.user_id,
            product_name=data.name,
            trait_type="origin",
            trait_value=data.origin,
            source="registration"
        )
        db.add(trait)

    user.registration_step = 2
    db.commit()
    db.refresh(product)

    print(f" 产品注册成功: {data.name} | {len(data.keywords)}个关键词已存⼊特征库")
    return {
        "product_id": product.id,
        "message": "产品信息已保存",
        "step": 2,
        "traits_saved": len(data.keywords) + (1 if data.description else 0)
    }


# ---------- 产品图⽚上传 ----------
@app.post("/api/product/{product_id}/image")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传产品主图，路径存⼊ products.main_image"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "产品不存在"})

    ext = Path(file.filename).suffix.lower() or ".jpg"
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = Path(UPLOAD_DIR) / filename

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    product.main_image = str(save_path)
    db.commit()
    print(f" 产品图⽚已保存: {save_path}")
    return {"success": True, "product_id": product_id, "image_path": str(save_path)}


@app.get("/api/product/{product_id}/image")
async def get_product_image(product_id: int, db: Session = Depends(get_db)):
    """返回产品图⽚ base64，供 Creation.vue ⾃动加载"""
    import base64 as b64mod

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not product.main_image:
        return JSONResponse(status_code=404, content={"detail": "暂⽆产品图⽚"})

    img_path = Path(product.main_image)
    if not img_path.exists():
        return JSONResponse(status_code=404, content={"detail": "图⽚文件不存在"})

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    ext = img_path.suffix.lower().replace(".", "")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    b64 = b64mod.b64encode(img_bytes).decode()
    return {"success": True, "image_base64": f"data:image/{mime};base64,{b64}", "filename": img_path.name}


# ---------- 编辑产品 ----------
class ProductUpdateRequest(BaseModel):
    name: str
    category: str
    origin: str
    keywords: List[str] = []
    description: Optional[str] = None


@app.put("/api/product/{product_id}")
async def update_product(product_id: int, data: ProductUpdateRequest, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "产品不存在"})

    try:
        product.name = data.name
        product.category = ProductCategory(data.category)
        product.origin = data.origin
        product.keywords = data.keywords
        product.description = data.description
        db.commit()
        print(f" 产品已更新: {data.name}")
        return {"success": True, "message": "产品信息已更新"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


# ---------- 删除产品 ----------
@app.delete("/api/product/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "产品不存在"})

    db.delete(product)
    db.commit()
    print(f" 产品已删除: {product.name}")
    return {"success": True, "message": "产品已删除"}


# ---------- 设为主推产品 ----------
@app.post("/api/product/{product_id}/set-primary")
async def set_primary_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse(status_code=404, content={"detail": "产品不存在"})

    db.query(Product).filter(Product.user_id == product.user_id).update({"is_primary": False})
    product.is_primary = True
    db.commit()
    print(f" 主推产品已切换为: {product.name}")
    return {"success": True, "message": f"{product.name} 已设为主推产品"}


# ---------- 特征记忆（ai_service 调⽤）----------
@app.post("/api/user/trait")
async def save_user_trait(data: TraitSaveRequest, db: Session = Depends(get_db)):
    """
    ai_service 调⽤此接⼝，将对话中提取的新特征存⼊数据库。
    例如：⽤户说"板栗很软糯"→ ai_service 提取 {type:texture, value:软糯} → 调⽤此接⼝保存
    """
    # 避免重复保存相同特征
    existing = db.query(UserTrait).filter(
        UserTrait.user_id == data.user_id,
        UserTrait.product_name == data.product_name,
        UserTrait.trait_value == data.trait_value
    ).first()

    if not existing:
        trait = UserTrait(
            user_id=data.user_id,
            product_name=data.product_name,
            trait_type=data.trait_type,
            trait_value=data.trait_value,
            source=data.source
        )
        db.add(trait)
        db.commit()
        print(f" 新特征已保存: [{data.product_name}] {data.trait_type}={data.trait_value}")
        return {"message": "特征已保存", "saved": True}
    else:
        return {"message": "特征已存在，跳过", "saved": False}


# ---------- 完整档案（供 ai_service 调⽤）----------
@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    返回⽤户完整档案：基本信息 + 主推产品 + 所有特征
    ai_service 在⽣成文案前调⽤此接⼝获取上下文
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse(status_code=404, content={"detail": "⽤户不存在"})

    # 主推产品
    primary = db.query(Product).filter(
        Product.user_id == user_id,
        Product.is_primary == True
    ).first()

    # 所有产品
    all_products = db.query(Product).filter(Product.user_id == user_id).all()

    # 所有特征
    all_traits = db.query(UserTrait).filter(UserTrait.user_id == user_id).all()

    return {
        "user_id": user_id,
        "username": user.full_name or user.company_name or "⽤户",
        "user_type": user.user_type.value,
        "company_name": user.company_name,
        "region": user.region,
        "phone": user.phone,
        "registration_step": user.registration_step,

        # 主推产品详情（AI ⽣成文案的主要依据）
        "primary_product": {
            "name": primary.name,
            "category": primary.category.value,
            "category_label": CATEGORY_LABELS.get(primary.category.value, ""),
            "origin": primary.origin,
            "keywords": primary.keywords or [],
            "description": primary.description or ""
        } if primary else None,

        # 所有产品列表
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value,
                "origin": p.origin,
                "keywords": p.keywords or [],
                "is_primary": p.is_primary
            } for p in all_products
        ],

        # 全部特征（注册+对话中学习到的）
        "traits": [
            {
                "product_name": t.product_name,
                "trait_type": t.trait_type,
                "trait_value": t.trait_value,
                "source": t.source,
                "created_at": t.created_at.isoformat() if t.created_at else ""
            } for t in all_traits
        ]
    }


@app.get("/api/user/{user_id}/traits")
async def get_product_traits(user_id: int, product_name: Optional[str] = None, db: Session = Depends(get_db)):
    """获取某个产品的所有已知特征（可选按产品名过滤）"""
    query = db.query(UserTrait).filter(UserTrait.user_id == user_id)
    if product_name:
        query = query.filter(UserTrait.product_name == product_name)

    traits = query.all()
    return {
        "traits": [
            {"type": t.trait_type, "value": t.trait_value, "source": t.source}
            for t in traits
        ]
    }


# ---------- ⽤户补充信息（⼯具箱，配合向量数据库）----------
class UserExtraInfoRequest(BaseModel):
    user_id: int
    text: str


@app.post("/api/user/extra-info")
async def save_extra_info(data: UserExtraInfoRequest):
    """保存⽤户补充的公司/个⼈信息到向量数据库"""
    try:
        from vector_memory_v2 import get_vector_memory
        vm = get_vector_memory()
        vm.add_memory(data.user_id, data.text, source="toolbox")
        return {"success": True, "saved_chunks": 1, "message": "已存入向量库"}
    except Exception as e:
        print(f" 向量存储失败：{e}")
        return {"success": False, "message": f"存储失败：{e}"}


@app.get("/api/user/{user_id}/extra-info")
async def get_extra_info(user_id: int):
    """获取⽤户已存储的补充信息"""
    try:
        from vector_memory_v2 import get_vector_memory
        memories = get_vector_memory().list_memories(user_id)
        # 返回格式：[{"id": hash, "text": ..., "has_vector": bool}, ...]
        items = [{"id": m.get("text", "")[:16], "text": m["text"]} for m in memories]
        return {"success": True, "items": items, "count": len(items)}
    except Exception as e:
        print(f"读取向量记忆失败：{e}")
        return {"success": True, "items": [], "count": 0}


@app.delete("/api/user/{user_id}/extra-info")
async def delete_extra_info(user_id: int):
    """清除⽤户的补充信息"""
    try:
        from vector_memory_v2 import get_vector_memory
        get_vector_memory().clear_memories(user_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}
    
@app.delete("/api/user/{user_id}/extra-info/{chunk_id}")
async def delete_extra_info_item(user_id: int, chunk_id: str):
    """删除向量库中单条记忆（按 hash 匹配）"""
    try:
        from vector_memory_v2 import get_vector_memory
        import os, json as _json
        vm = get_vector_memory()
        path = vm._file_path(user_id)
        if not os.path.exists(path):
            return {"success": False, "message": "无记忆文件"}
        with open(path, "r", encoding="utf-8") as f:
            records = _json.load(f)
        # chunk_id 约定为 text 前16字符，或 hash
        before = len(records)
        records = [r for r in records if r.get("hash") != chunk_id and r.get("text", "")[:16] != chunk_id]
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(records, f, ensure_ascii=False)
        deleted = before - len(records)
        print(f"✅ 已删除用户{user_id}的记忆 {deleted} 条")
        return {"success": True, "message": f"已删除{deleted}条记忆"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ============ 运⾏ ============
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print(" 农产品信息登记系统 v2 启动")
    print("=" * 60)
    print(" 端⼝: http://localhost:5000")
    print(" 数据库: agriculture.db（SQLite）")
    print("")
    print("数据库表结构：")
    print(" users - ⽤户账号（⼀个账号=⼀家企业/农户）")
    print(" products - 产品信息（⼀⽤户可多产品）")
    print(" user_traits - 特征记忆（注册关键词+对话中学到的）")
    print("")
    print("关键接⼝：")
    print(" POST /api/auth/register 注册（第⼀步）")
    print(" POST /api/product/register 产品登记（第⼆步）")
    print(" POST /api/user/trait ai_service保存新特征")
    print(" GET /api/user/{id}/profile 获取完整⽤户档案")
    print("=" * 60)

    # 测试密码加密
    test_pwd = "123456"
    hashed = get_password_hash(test_pwd)
    print(f"密码加密测试: '{test_pwd}' → {hashed[:30]}...")
    print("=" * 60)

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)