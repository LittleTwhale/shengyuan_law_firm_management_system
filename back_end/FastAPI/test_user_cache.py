# test_user_cache.py
"""
用户缓存功能的简单测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from package.core.user_cache import user_cache

def test_user_cache():
    print("=== 用户缓存功能测试 ===")

    # 测试无效token
    print("1. 测试无效token:")
    result1 = user_cache.get_user_display_name("invalid_token")
    print(f"   结果: {result1}")

    # 测试空token
    print("2. 测试空token:")
    result2 = user_cache.get_user_display_name("")
    print(f"   结果: {result2}")

    # 测试缓存统计
    print("3. 缓存统计:")
    stats = user_cache.get_cache_stats()
    print(f"   统计信息: {stats}")

    # 测试缓存清理
    print("4. 测试缓存清理:")
    user_cache.clear_cache()
    stats_after_clear = user_cache.get_cache_stats()
    print(f"   清理后统计: {stats_after_clear}")

    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_user_cache()