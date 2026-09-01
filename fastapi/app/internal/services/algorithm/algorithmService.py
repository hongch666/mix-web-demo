from functools import lru_cache
from typing import Any

from app.core.constants import AlgorithmConstants, Scripts
from app.internal.schemas import ScoreWeightItem, ScriptParamItem


class AlgorithmService:
    """搜索排序权重服务 — 所有排序公式权重的权威来源"""

    def get_weights(self) -> dict[str, Any]:
        weights: list[ScoreWeightItem] = []
        for key, value, desc in AlgorithmConstants.WEIGHT_DEFINITIONS:
            weights.append(
                ScoreWeightItem(
                    key=key,
                    value=round(float(value), 4),
                    description=desc,
                )
            )
        return {"weights": weights}

    def get_es_script(self) -> dict[str, Any]:
        """获取 ES Painless 搜索脚本

        返回使用 params.xxx 占位符的脚本模板，由 GoZero 调用方在运行时通过
        elastic.NewScript(script).Param(name, value) 方式传入具体的权重值后使用。
        """
        return {"es_script": Scripts.ES_SEARCH_SCRIPT}

    def get_script_params(self) -> dict[str, Any]:
        """获取脚本参数名映射

        返回每个权重 key 在 Painless 脚本中对应的 params.xxx 参数名。
        GoZero 调用方根据此映射关系使用 elastic.NewScript(script).Param(paramName, value)
        组装 ES 脚本查询，无需在 GoZero 端硬编码参数名常量。
        """
        params: list[ScriptParamItem] = []
        for weight_key, param_name, desc in AlgorithmConstants.SCRIPT_PARAM_MAPPINGS:
            params.append(
                ScriptParamItem(
                    weight_key=weight_key,
                    param_name=param_name,
                    description=desc,
                )
            )
        return {"script_params": params}


@lru_cache
def get_algorithm_service() -> AlgorithmService:
    return AlgorithmService()
