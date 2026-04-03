# utils/keywords_helper.py
import re
from typing import List, Set


def get_valid_keywords(name_set: set) -> list:
    """
    清洗并提取有效的模糊匹配关键字
    1. 过滤常见的无意义词（黑名单）
    2. 智能剥离常见后缀（扩大匹配面）
    3. 过滤掉长度为1的单字
    """
    # 常见无意义词黑名单（全匹配时丢弃）
    stop_words = {
        "公司", "有限公司", "有限责任公司", "集团", "股份", "股份有限公司",
        "分公司", "厂", "中心", "工作室", "企业", "合伙企业", "合伙",
        "银行", "支行", "分行", "法院", "检察院", "公安局", "派出所",
        "局", "厅", "局集团", "局集团有限公司",

        # ====== 高频银行泛指词汇（防止灾难性模糊扫描） ======
        "农村商业银行", "中国农业银行", "中国建设银行", "中国工商银行", "中国银行",
        "交通银行", "邮政储蓄银行", "农商行", "信用社"
        # ================================================================
    }

    # 2. 常见后缀 (用于从尾部剥离)
    suffixes_to_strip = [
        "有限责任公司", "股份有限公司", "有限公司", "分公司", "公司",
        "集团", "支行", "分行", "中心", "厂", "工作室"
    ]

    # 3. 常见非标准地域/修饰前缀 (用于从头部剥离)
    PREFIXES_TO_STRIP = [
        "中国", "中华", "湘西", "吉首",
    ]

    valid_keywords = []
    for name in name_set:
        name = name.strip()

        # 如果名字“完全等于”泛化词汇（如只填了"农村商业银行"），直接抛弃不作为模糊词
        # 它们在主干逻辑中依然会参与 exact 确切匹配，不用担心漏掉
        if not name or name in stop_words:
            continue

        # 智能提取核心词：如果以常见后缀结尾，且去掉后缀后主体长度 >= 2，则去掉后缀
        # 目的：将输入的 "腾讯计算机有限公司" 变成 "腾讯计算机"，去数据库里模糊匹配
        core_name = name
        # --- 第一步：剥离非标准前缀 (如"湘西") ---
        for prefix in PREFIXES_TO_STRIP:
            # 确保剥离后，剩下的字数 >= 2 (防止"中国网"剥离后只剩"网")
            if core_name.startswith(prefix) and len(core_name) - len(prefix) >= 2:
                core_name = core_name[len(prefix):]
                break  # 剥离一个最长的即可

        # --- 第二步：剥离标准行政区划前缀 (正则匹配"省/市/县/区") ---
        while True:
            new_name = re.sub(r'^[\u4e00-\u9fa5]{1,4}(省|市|县|区|自治州|新区)', '', core_name)
            if new_name == core_name:
                break
            core_name = new_name

        # --- 第三步：剥离常见企业后缀 ---
        for suffix in suffixes_to_strip:
            if core_name.endswith(suffix) and len(core_name) - len(suffix) >= 2:
                core_name = core_name[:-len(suffix)]
                break

        # --- 第四步：兜底安全校验 ---
        # 如果长度为1（单字），或者剩下的核心词依然是个无意义的词，丢弃
        if len(core_name) > 1 and core_name not in stop_words:
            # 防爆墙：如果剩下的词正好是“湖南”、“湘西”这类纯地域词，也应丢弃(按需可在STOP_WORDS补充)
            valid_keywords.append(core_name)

    return valid_keywords


def determine_party_side(party_type: str) -> str:
    """
    通过模糊匹配判断当事人所属阵营 (A: 主动方, B: 被动方, Unknown: 未知)
    注意：必须先判断 B 阵营，防止“被申请人”被误判为包含“申请人”的 A 阵营。
    """
    if not party_type:
        return "Unknown"

    party_type = party_type.strip()

    # 优先判断 B 阵营（被动方）
    side_b_keywords = ["被告", "被申请", "被上诉", "被执行", "申诉被", "反诉原告"]
    if any(keyword in party_type for keyword in side_b_keywords):
        return "B"

    # 其次判断 A 阵营（主动方）
    side_a_keywords = ["原告", "申请", "上诉", "起诉", "执行人", "申诉人"]
    if any(keyword in party_type for keyword in side_a_keywords):
        return "A"

    return "Unknown"