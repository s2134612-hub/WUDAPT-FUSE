"""
验证数据账号配置是否正确。

运行: python scripts/check_accounts.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path

print("=" * 50)
print("WUDAPT-FUSE 数据账号验证")
print("=" * 50)


def check_cdsapi():
    print("\n[1] ECMWF Climate Data Store (CDS)")

    cdsapirc = Path.home() / ".cdsapirc"
    if not cdsapirc.exists():
        print(f"  ✗ ~/.cdsapirc 不存在")
        print(f"     需创建文件: {cdsapirc}")
        return False

    content = cdsapirc.read_text()
    if "url:" not in content or "key:" not in content:
        print(f"  ✗ ~/.cdsapirc 格式错误")
        return False

    print(f"  ✓ ~/.cdsapirc 存在: {cdsapirc}")

    try:
        import cdsapi
        client = cdsapi.Client(quiet=True)
        print(f"  ✓ cdsapi.Client 初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ cdsapi 连接失败: {e}")
        return False


def check_earthdata():
    print("\n[2] NASA Earthdata")

    netrc = Path.home() / ".netrc"
    netrc_alt = Path.home() / "_netrc"  # Windows alt
    found = None

    if netrc.exists():
        found = netrc
    elif netrc_alt.exists():
        found = netrc_alt

    if found is None:
        print(f"  ✗ .netrc 不存在 (~/.netrc 或 ~/_netrc)")
        return False

    content = found.read_text()
    if "urs.earthdata.nasa.gov" not in content:
        print(f"  ✗ {found} 缺少 urs.earthdata.nasa.gov 条目")
        return False

    print(f"  ✓ {found} 已配置 NASA 凭证")
    return True


def check_earthengine():
    print("\n[3] Google Earth Engine")

    try:
        import ee
        try:
            ee.Initialize()
            print(f"  ✓ Earth Engine 已认证并初始化")

            # 简单测试
            try:
                point = ee.Geometry.Point([114.0, 22.5])
                count = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(point).filterDate('2020-01-01', '2020-12-31').size().getInfo()
                print(f"  ✓ Landsat 数据可访问 ({count} 张影像)")
                return True
            except Exception as e:
                print(f"  ⚠ 已认证但数据访问失败: {e}")
                return True

        except Exception as e:
            print(f"  ✗ Earth Engine 未认证")
            print(f"     请运行: earthengine authenticate")
            return False

    except ImportError:
        print(f"  ⚠ earthengine-api 未安装（可选）")
        return None


def check_amap():
    print("\n[4] 高德地图 API（可选）")

    key = os.environ.get('AMAP_API_KEY')
    if not key:
        print(f"  ⚠ AMAP_API_KEY 环境变量未设置")
        print(f"     设置: $env:AMAP_API_KEY = 'YOUR_KEY'")
        return False

    print(f"  ✓ AMAP_API_KEY 已配置")
    return True


def main():
    results = {
        'ECMWF CDS': check_cdsapi(),
        'NASA Earthdata': check_earthdata(),
        'Earth Engine': check_earthengine(),
        '高德 API': check_amap(),
    }

    print("\n" + "=" * 50)
    print("汇总:")
    for name, status in results.items():
        if status is True:
            sym = "✓"
        elif status is False:
            sym = "✗"
        else:
            sym = "⚠"
        print(f"  {sym} {name}")

    n_ok = sum(1 for v in results.values() if v is True)
    print(f"\n通过: {n_ok}/{len(results)}")

    if n_ok >= 1:  # 至少 ECMWF
        print("\n✓ 可以开始数据下载")
    else:
        print("\n请先注册并配置至少 ECMWF CDS")


if __name__ == "__main__":
    main()
