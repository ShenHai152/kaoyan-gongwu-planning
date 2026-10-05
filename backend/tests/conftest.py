import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base

SAMPLE_HEADER = [
    "年份",
    "院校名称",
    "院校类型",
    "专业名称",
    "专业代码",
    "所属院系",
    "专硕/学硕",
    "总分",
    "总分线差",
    "政治",
    "政治线差",
    "外语",
    "外语线差",
    "专业课一",
    "专业课一线差",
    "专业课二",
    "专业课二线差",
    "备注",
    "所在地",
    "隶属",
    "985",
    "211",
    "双一流",
    "AB区",
    "自划线",
    "招生官网",
    "招生电话",
    "招生邮箱",
    "学校地址",
]

SAMPLE_ROWS = [
    [
        "2026.0",
        "遵义医科大学",
        "医药类",
        "临床检验诊断学",
        "100208",
        "第一临床学院",
        "学硕",
        "325.0",
        "↑41",
        "50.0",
        "↑17",
        "50.0",
        "↑17",
        "99.0",
        "",
        "0.0",
        "",
        "",
        "贵州",
        "贵州省",
        "否",
        "否",
        "否",
        "B",
        "否",
        "https://example.edu.cn/",
        "0000-00000000",
        "",
        "新蒲校区",
    ],
    [
        "2026.0",
        "上海体育大学",
        "体育类",
        "体育人文社会学",
        "040301",
        "体育教育学院",
        "学硕",
        "300.0",
        "↑10",
        "40.0",
        "↑5",
        "40.0",
        "↑5",
        "120.0",
        "",
        "0.0",
        "",
        "",
        "上海",
        "上海市",
        "否",
        "否",
        "是",
        "A",
        "否",
        "https://example.edu.cn/",
        "0000-00000000",
        "",
        "上海市杨浦区",
    ],
    [
        "2025.0",
        "上海体育大学",
        "体育类",
        "体育人文社会学",
        "040301",
        "体育教育学院",
        "学硕",
        "295.0",
        "↑8",
        "39.0",
        "↑4",
        "39.0",
        "↑4",
        "118.0",
        "",
        "0.0",
        "",
        "",
        "上海",
        "上海市",
        "否",
        "否",
        "是",
        "A",
        "否",
        "https://example.edu.cn/",
        "0000-00000000",
        "",
        "上海市杨浦区",
    ],
]


@pytest.fixture()
def sample_admission_rows():
    return SAMPLE_HEADER, SAMPLE_ROWS


GEN1_HEADER = [
    "年份",
    "学校名称_链接",
    "学校名称",
    "院系名称_链接",
    "院系名称",
    "专业代码",
    "专业名称_链接",
    "专业名称",
    "总分",
    "政治__管综",
    "外语",
    "业务课_一",
    "业务课_二",
]

GEN1_ROWS = [
    [
        "2017.0",
        "https://example.edu.cn",
        "兰州大学",
        "https://example.edu.cn",
        "药学院",
        "100703.0",
        "https://example.edu.cn",
        "生药学",
        "295.0",
        "50.0",
        "50.0",
        "150.0",
        "-",
    ],
    [
        "2017.0",
        "https://example.edu.cn/a",
        "兰州大学",
        "https://example.edu.cn/a",
        "药学院",
        "100704.0",
        "https://example.edu.cn/a",
        "药物分析学",
        "-",
        "-",
        "-",
        "-",
        "-",
    ],
    [
        "2017.0",
        "https://example.edu.cn/b",
        "兰州大学",
        "https://example.edu.cn/b",
        "药学院",
        "100704.0",
        "https://example.edu.cn/b",
        "药物分析学",
        "300.0",
        "48.0",
        "48.0",
        "160.0",
        "-",
    ],
]

GEN2_HEADER = [
    "年份",
    "学校",
    "硕士类型",
    "专业代码",
    "专业名称",
    "总分",
    "政治",
    "英语",
    "专业课一",
    "专业课二",
    "备注",
    "学校省份",
    "学校属性",
    "学校官网",
    "学校研究生官网",
    "学校电话",
    "学校邮箱",
    "学校地址",
    "隶属",
    "硕士点",
    "博士点",
    "国家重点学科",
    "重点实验室",
]

GEN2_ROWS = [
    [
        "2020",
        "武汉大学",
        "专业型硕士",
        "125601",
        "工程管理",
        "195",
        "44",
        "50",
        "100",
        "88",
        "",
        "湖北",
        "高等院校  综合类  985  211  双一流  自划线  A区",
        "https://example.edu.cn/",
        "https://example.edu.cn/",
        "0000-00000000",
        "",
        "湖北省武汉市",
        "教育部",
        "59",
        "49",
        "41",
        "24",
    ],
    [
        "2021",
        "武汉大学",
        "学术型硕士",
        "120100",
        "管理科学与工程",
        "360",
        "60",
        "60",
        "90",
        "90",
        "",
        "湖北",
        "高等院校  综合类  985  211  双一流  A区",
        "https://example.edu.cn/",
        "https://example.edu.cn/",
        "0000-00000000",
        "",
        "湖北省武汉市",
        "教育部",
        "59",
        "49",
        "41",
        "24",
    ],
]


@pytest.fixture()
def gen1_rows():
    return GEN1_HEADER, GEN1_ROWS


@pytest.fixture()
def gen2_rows():
    return GEN2_HEADER, GEN2_ROWS


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _enable_fks(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    factory = sessionmaker(bind=engine)
    with factory() as s:
        yield s


ENROLL_A_HEADER = [
    "院校代码",
    "院校名称",
    "所在城市",
    "院校层级",
    "考试方式",
    "院系所",
    "专业",
    "学习方式",
    "研究方向",
    "指导老师",
    "拟招人数",
    "政治",
    "外语",
    "业务课一",
    "业务课二",
    "备注",
]

ENROLL_A_ROWS = [
    [
        "91020",
        "海军军医大学",
        "上海市",
        "_,_,双一流",
        "统考",
        "(113)长征医院",
        "(105101)(专业学位)内科学",
        "全日制",
        "(19)心内-冠心病-某某",
        "某某",
        "专业：4(不含推免)",
        "(101)思想政治理论",
        "(201)英语（一）",
        "(306)临床医学综合能力（西医）",
        "(--)无",
        "",
    ],
    [
        "10153",
        "沈阳建筑大学",
        "沈阳市",
        "_,_,_",
        "统考",
        "(008)交通与测绘工程学院",
        "(082303)交通运输规划与管理",
        "全日制",
        "(01)交通管理与控制",
        "详见目录",
        "专业：4(不含推免)",
        "(101)思想政治理论",
        "(202)俄语",
        "(301)数学（一）",
        "(816)交通工程学",
        "",
    ],
]

ENROLL_B_HEADER = [
    "年份",
    "院校名称",
    "院校类型",
    "门类",
    "一级学科",
    "专业名称",
    "专业代码",
    "所属院系",
    "专硕/学硕",
    "研究方向",
    "学习方式",
    "招生人数",
    "招生人数说明",
    "考试方式",
    "考试科目",
    "所在地",
    "隶属",
    "985",
    "211",
    "双一流",
    "AB区",
    "自划线",
    "招生官网",
    "招生电话",
    "招生邮箱",
    "学校地址",
    "参考书目",
]

ENROLL_B_ROWS = [
    [
        "2026.0",
        "湖北大学",
        "综合类",
        "哲学",
        "哲学",
        "哲学",
        "010100",
        "哲学学院",
        "学术型硕士",
        "（04）逻辑学",
        "全日制",
        "46.0",
        "【招生人数为专业招生总数，非方向人数】",
        "统考",
        "①(101)思想政治理论\n②(201)英语（一）",
        "湖北",
        "湖北省",
        "否",
        "否",
        "否",
        "A",
        "否",
        "https://example.edu.cn/",
        "0000-00000000",
        "example@example.com",
        "武汉市",
        "701中国哲学史",
    ],
]


@pytest.fixture()
def enroll_gen_a_rows():
    return ENROLL_A_HEADER, ENROLL_A_ROWS


@pytest.fixture()
def enroll_gen_b_rows():
    return ENROLL_B_HEADER, ENROLL_B_ROWS
