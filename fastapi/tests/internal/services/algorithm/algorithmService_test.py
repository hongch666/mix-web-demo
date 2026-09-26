from app.core.constants import AlgorithmConstants, Scripts
from app.internal.schemas import ScoreWeightItem, ScriptParamItem
from app.internal.services.algorithm.algorithmService import (
    AlgorithmService,
    get_algorithm_service,
)


# 权重列表与 WEIGHT_DEFINITIONS 的数量、键值和描述一致
def test_get_weights_matches_definitions() -> None:
    result = AlgorithmService().get_weights()

    weights = result["weights"]
    assert len(weights) == len(AlgorithmConstants.WEIGHT_DEFINITIONS)
    assert all(isinstance(item, ScoreWeightItem) for item in weights)
    expected = {
        key: round(float(value), 4)
        for key, value, _ in AlgorithmConstants.WEIGHT_DEFINITIONS
    }
    assert {item.key: item.value for item in weights} == expected
    assert all(item.description for item in weights)


# 权重项按 WEIGHT_DEFINITIONS 的声明顺序返回
def test_get_weights_preserves_definitions_order() -> None:
    weights = AlgorithmService().get_weights()["weights"]

    assert [item.key for item in weights] == [
        key for key, _, _ in AlgorithmConstants.WEIGHT_DEFINITIONS
    ]


# 返回 ES 搜索脚本模板常量
def test_get_es_script_returns_canonical_template() -> None:
    assert AlgorithmService().get_es_script() == {"es_script": Scripts.ES_SEARCH_SCRIPT}


# 脚本参数与 SCRIPT_PARAM_MAPPINGS 的权重键映射一一对应
def test_get_script_params_maps_each_weight_key() -> None:
    params = AlgorithmService().get_script_params()["script_params"]

    assert len(params) == len(AlgorithmConstants.SCRIPT_PARAM_MAPPINGS)
    assert all(isinstance(item, ScriptParamItem) for item in params)
    assert {(item.weight_key, item.param_name) for item in params} == {
        (key, name) for key, name, _ in AlgorithmConstants.SCRIPT_PARAM_MAPPINGS
    }
    assert all(item.description for item in params)


# 工厂函数返回同一缓存单例
def test_factory_returns_cached_singleton() -> None:
    assert get_algorithm_service() is get_algorithm_service()
